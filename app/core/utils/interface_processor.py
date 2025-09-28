import re
from typing import List, Dict, Set
from collections import defaultdict, OrderedDict

from app.core.logging_setup import logger

logger = logger.bind(component="DeviceUtils")

physical_ifTypes = {6, 117}  # Можно расширить при необходимости


class InterfaceProcessor:
    INTERFACE_ALIASES = {
        r"^Gi(\d+(?:/\d+)+)$": r"GigabitEthernet\1",
        r"^Te(\d+(?:/\d+)+)$": r"TenGigabitEthernet\1",
        r"^Fa(\d+(?:/\d+)+)$": r"FastEthernet\1",
        r"^Fo(\d+(?:/\d+)+)$": r"FortyGigabitEthernet\1",
        r"^Po0*(\d+)$": r"Port-channel\1",
        r"^Lo0*(\d+)$": r"Loopback\1",
        r"^Vl(\d+)$": r"Vlan\1",
        r"^GE(\d+(?:/\d+)+)$": r"GigabitEthernet\1",
        r"^XGE(\d+(?:/\d+)+)$": r"TenGigabitEthernet\1",
        r"^gigabitethernet(\d+(?:/\d+)+)$": r"GigabitEthernet\1",
        r"^tengigabitethernet(\d+(?:/\d+)+)$": r"TenGigabitEthernet\1",
        r"^Eth-Trunk(\d+)$": r"Eth-Trunk\1",
        r"^NULL0*$": r"Null0",
        r"^Et(\d+(?:/\d+)*|\d+)$": r"Ethernet\1",
        r"^Ethernet(\d+(?:/\d+)*|\d+)$": r"Ethernet\1",
        r"^ge-\d+/\d+/\d+$": lambda m: "GigabitEthernet"
        + "".join(re.findall(r"\d+", m.group())),
        r"^xe-\d+/\d+/\d+$": lambda m: "TenGigabitEthernet"
        + "".join(re.findall(r"\d+", m.group())),
        r"^ae(\d+)$": r"AggregatedEthernet\1",
        r"^lo(\d+)$": r"Loopback\1",
        r"^G(\d+)$": r"GigabitEthernet0/0/\1",
        r"^T(\d+)$": r"TenGigabitEthernet0/0/\1",
        r"^Uplink(\d+)$": r"Uplink\1",
        r"^port(\d+)$": r"Port\1",
        r"^vlan(\d+)$": r"Vlan\1",
        r"^adsl(\d+)$": r"ADSL\1",
        r"^enet(\d+)$": r"Ethernet\1",
    }

    CATEGORIES = {
        "gigabitethernet": re.compile(r"^GigabitEthernet\d+(?:/\d+)*$", re.IGNORECASE),
        "tengigabitethernet": re.compile(
            r"^TenGigabitEthernet\d+(?:/\d+)*$", re.IGNORECASE
        ),
        "fastethernet": re.compile(r"^FastEthernet\d+(?:/\d+)*$", re.IGNORECASE),
        "fortygigethernet": re.compile(
            r"^FortyGigabitEthernet\d+(?:/\d+)*$", re.IGNORECASE
        ),
        "hundredgigethernet": re.compile(r"^HundredGigE\d+(?:/\d+)*$", re.IGNORECASE),
        "ethernet": re.compile(r"^Ethernet\d+(?:/\d+)*$", re.IGNORECASE),
        "adsl": re.compile(r"^ADSL\d+$", re.IGNORECASE),
        "enet": re.compile(r"^Ethernet\d+$", re.IGNORECASE),
        "uplink": re.compile(r"^Uplink\d+$", re.IGNORECASE),
        "eth-trunk": re.compile(r"^Eth-Trunk\d+$", re.IGNORECASE),
        "portchannel": re.compile(r"^Port-channel\d+$", re.IGNORECASE),
        "aggregatedethernet": re.compile(r"^AggregatedEthernet\d+$", re.IGNORECASE),
        "loopback": re.compile(r"^Loopback\d+$", re.IGNORECASE),
        "tunnel": re.compile(r"^Tunnel\d+$", re.IGNORECASE),
        "vlan": re.compile(r"^Vlan\d+$", re.IGNORECASE),
        "mgmt": re.compile(r"^Mgmt\d*$", re.IGNORECASE),
        "null": re.compile(r"^Null\d+$", re.IGNORECASE),
        "logical": re.compile(r"^Logical-int\s*\d+$", re.IGNORECASE),
        "port": re.compile(r"^Port\d+$", re.IGNORECASE),
        "numeric": re.compile(r"^\d+$"),
        "other": re.compile(r".*"),
        # Or create separate category if needed
    }

    PHYSICAL_CATEGORIES = {
        "ethernet",
        "fastethernet",
        "gigabitethernet",
        "tengigabitethernet",
        "hundredgigethernet",
        "fortygigethernet",
        "adsl",
        "enet",  # Add if these are physical interfaces
    }

    @classmethod
    def normalize_interface_name(
        cls, name: str | List[str], index: int | None = None
    ) -> str | List[str]:
        if isinstance(name, list):
            # logger.info(f"Normalizing list of interface names (count={len(name)})")
            return [cls.normalize_interface_name(n) for n in name]

        if not isinstance(name, str):
            # logger.error(f"Invalid interface name type: {type(name)} (value: {name})")
            raise TypeError(f"Expected string or list of strings, got {type(name)}")

        original_name = name
        name = name.strip()
        if name.lower() == "ethernet interface" and index is not None:
            return f"Ethernet{index}"
        # logger.info(f"Normalizing interface name: '{original_name}'")

        for pattern, repl in cls.INTERFACE_ALIASES.items():
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                normalized = (
                    repl(match)
                    if callable(repl)
                    else re.sub(pattern, repl, name, flags=re.IGNORECASE)
                )
                # logger.info(f"Interface normalized: '{original_name}' -> '{normalized}' (pattern: '{pattern}')")
                return normalized

        # logger.info(f"No matching pattern found for interface: {name}")
        return name

    @classmethod
    def categorize_interfaces(
        cls, iface_list: List[str], only_physical: bool = False
    ) -> Dict[str, List[str]]:
        # logger.info(f"Categorizing interfaces (count={len(iface_list)}, only_physical={only_physical})")
        categorized = defaultdict(list)
        stats = {"total": 0, "physical": 0, "logical": 0}

        for raw_iface in iface_list:
            iface = cls.normalize_interface_name(raw_iface)
            stats["total"] += 1

            for category, pattern in cls.CATEGORIES.items():
                if pattern.fullmatch(iface):
                    if only_physical and category not in cls.PHYSICAL_CATEGORIES:
                        # logger.info(f"Skipping non-physical interface: {iface} (category: {category})")
                        stats["logical"] += 1
                        break

                    categorized[category].append(iface)
                    if category in cls.PHYSICAL_CATEGORIES:
                        stats["physical"] += 1
                    # logger.info(f"Interface categorized: {iface} -> {category}")
                    break

        # logger.info(f"Categorization stats: {stats}")
        return categorized

    @staticmethod
    def sort_interfaces(interface_list: List[str]) -> List[str]:
        # logger.info(f"Sorting interfaces (count={len(interface_list)})")

        def iface_key(iface: str):
            nums = list(map(int, re.findall(r"\d+", iface)))
            return (iface.lower(), *nums)

        sorted_list = sorted(interface_list, key=iface_key)
        # logger.info(f"Sorted interfaces: {sorted_list[:10]} (first 10)")
        return sorted_list

    @classmethod
    def process_interfaces(
        cls, raw_list: List[str], only_physical: bool = False
    ) -> Dict[str, List[str]]:
        # logger.info(f"Processing interfaces (count={len(raw_list)}, only_physical={only_physical})")

        categorized = cls.categorize_interfaces(raw_list, only_physical=only_physical)
        result = {
            category: cls.sort_interfaces(interfaces)
            for category, interfaces in categorized.items()
        }

        total = sum(len(v) for v in result.values())
        # logger.info(f"Interfaces processing completed (categories_count={len(result)}, total_interfaces={total})")
        return result

    @staticmethod
    def merge_and_sort_interfaces(
        indexes: List[int], aliases: List[str], only_physical: bool = False
    ) -> OrderedDict:
        # logger.info(f"Merging and sorting interfaces (indexes={len(indexes)}, aliases={len(aliases)}, only_physical={only_physical})")

        if len(indexes) != len(aliases):
            # logger.error(f"Length mismatch: indexes={len(indexes)}, aliases={len(aliases)}")
            raise ValueError(
                f"Length mismatch: indexes({len(indexes)}) != aliases({len(aliases)})"
            )

        normalized_aliases = [
            InterfaceProcessor.normalize_interface_name(a, i)
            for i, a in enumerate(aliases, start=1)
        ]

        # logger.info(f"Normalized interface names: {normalized_aliases[:10]}")

        if only_physical:
            categorized = InterfaceProcessor.categorize_interfaces(
                normalized_aliases, only_physical=True
            )
            physical_set = {
                iface for interfaces in categorized.values() for iface in interfaces
            }

            # 💡 Если все alias не попали в физические категории — fallback по позиции
            if not physical_set and all(
                alias.lower() == "ethernet interface" for alias in normalized_aliases
            ):
                # logger.warning("All aliases are generic. Falling back to index-based Ethernet labeling.")
                fallback = [(idx, f"Ethernet{idx}") for idx in indexes]
                result = OrderedDict(fallback)
                # logger.info(f"Fallback physical map generated: {len(result)} entries.")
                return result

            filtered = [
                (idx, alias)
                for idx, alias in zip(indexes, normalized_aliases)
                if alias in physical_set
            ]
            # logger.info(f"Filtered physical interfaces: {len(filtered)} of {len(indexes)}")
        else:
            filtered = list(zip(indexes, normalized_aliases))

        sorted_pairs = sorted(filtered, key=lambda x: x[0])
        result = OrderedDict(sorted_pairs)
        # logger.info(f"Merge and sort completed. Total: {len(result)} entries.")
        return result

    @classmethod
    def filter_physical_interfaces(cls, interfaces: List[str]) -> List[str]:
        # logger.info(f"Filtering physical interfaces (input_count={len(interfaces)})")
        normalized = [cls.normalize_interface_name(i) for i in interfaces]
        categorized = cls.categorize_interfaces(normalized, only_physical=True)

        physical_ifaces = []
        for category, iface_list in categorized.items():
            physical_ifaces.extend(iface_list)
            # logger.info(f"Category '{category}': {len(iface_list)} interfaces")

        sorted_result = cls.sort_interfaces(physical_ifaces)
        # logger.info(f"Filtered {len(sorted_result)} physical interfaces from {len(interfaces)} input")
        return sorted_result

    @classmethod
    def extract_physical_ids(cls, iface_map: OrderedDict[int, str]) -> List[int]:
        # logger.info(f"Extracting physical interface IDs (map_size={len(iface_map)})")
        physical_ids = []

        for idx, name in iface_map.items():
            normalized = cls.normalize_interface_name(name)
            categorized = cls.categorize_interfaces([normalized], only_physical=True)

            if categorized:
                physical_ids.append(idx)
                # logger.info(f"Found physical interface (index={idx}, name={normalized})")

        # logger.info(f"Extracted {len(physical_ids)} physical IDs out of {len(iface_map)} total")
        return physical_ids

    @classmethod
    def extract_physical_ifNames(cls, iface_map: OrderedDict[int, str]) -> List[str]:
        # logger.info(f"Extracting physical interface IDs (map_size={len(iface_map)})")
        physical_names = []

        for idx, name in iface_map.items():
            normalized = cls.normalize_interface_name(name)
            categorized = cls.categorize_interfaces([normalized], only_physical=True)

            if categorized:
                physical_names.append(name)
                # logger.info(f"Found physical interface (index={name}, name={normalized})")

        # logger.info(f"Extracted {len(physical_names)} physical IDs out of {len(iface_map)} total")
        return physical_names

    @classmethod
    def filter_physical_by_ifType(
        ifIndex_list: List[int], ifType_map: Dict[int, int]
    ) -> List[int]:
        return [idx for idx in ifIndex_list if ifType_map.get(idx) in physical_ifTypes]
