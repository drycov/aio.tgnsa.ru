import json

data ={
  "models": {
    "S2350": "Huawei S2350-28TP-EI-AC",
    "S2700-18TP-SI-AC": "Huawei S2700-18TP-SI-AC",
    "S2320": "Huawei S2320-28TP-EI-AC",
    "S5320-28TP-LI-AC": "Huawei S5320-28TP-LI-AC",
    "S5320-28P-LI-AC": "Huawei S5320-28P-LI-AC",
    "S6320-54C-EI-48S-AC": "Huawei S6320-54C-EI-48S-AC",
    "S5700-26X-SI-12S-AC": "Huawei S5700-26X-SI-12S-AC",
    "Huawei Integrated Access Software": "Huawei SmartAX MA5616",
    "DGS-3420-28SC": "Dlink DGS-3420-28SC",
    "DGS-3620-28SC": "Dlink DGS-3620-28SC",
    "MES2324FB": "Eltex MES2324FB",
    "MES2324P": "Eltex MES2324P",
    "MES3324F": "Eltex MES3324F",
    "MES3308F": "Eltex MES3308F",
    "MES3316F": "Eltex MES3316F",
    "MES2428": "Eltex MES2428",
    "ZXR10 2928": "ZTE 2928E",
    "DES-3200-26": "D-Link DES-3200-26",
    "DES-3200-10": "D-Link DES-3200-10",
    "DES-3200-28": "D-Link DES-3200-28",
    "DES-1228/ME": "D-Link DES-1228/ME",
    "DES-1210-28/ME/B2": "D-Link DES-1210-28/ME/B2",
    "DES-1210-28": "D-Link DES-1210-28",
    "DES-1210-28/ME/B3": "D-Link DES-1210-28/ME/B3",
    "DGS-3000-10TC": "D-Link DGS-3000-10T",
    "DGS-3000-26TC": "D-Link DGS-3000-26TC",
    "Tp-Link T2700G-28TQ": "Tp-Link T2700G-28TQ",
    "Tp-Link T2600G-28TS": "Tp-Link T2600G-28TS",
    "Tp-Link TL-SL2428": "Tp-Link TL-SL2428",
    "Tp-Link TL-1600G-52PS": "Tp-Link TL-1600G-52PS",
    "CRS326-24G-2S+": "Mikrotik CRS326",
    "CRS112": "Mikrotik CRS112",
    "RB2011LS": "Mikrotik RB2011LS",
    "RB760": "Mikrotik RB760iGS",
    "RB SXT": "MikroTik SXT SA5",
    "RB911G-5HPacD": "Mikrotik NetBox 5",
    "CSS326-24G-2S+": "Mikrotik CSS326",
    "SNR-S2962-24T": "SNR S2962-24T",
    "SNR-S2995G-24FX": "SNR S2995G",
    "SNR-S2985G-24T": "SNR S2985G 24T",
    "SNR-S2985G-8T": "SNR S2985G 8T",
    "SNR-S2982G-24TE": "SNR S2982G 24T",
    "IES-612": "ZyXEL IES-612",
    "IES1248": "ZyXEL IES1248-51",
    "ZyXEL IES-1000/SAM1008": "ZyXEL SAM1008",
    "SG200-26": "Cisco SG200-26",
    "LinkSys SPS 208G": "LinkSys SPS 208G",
    "ME360x_t": "Cisco IOS ME3600",
    "ASR901": "Cisco IOS ASR901",
    "ASR9K": "Cisco IOS ASR9001",
    "C2960": "Cisco C2960",
    "LPOS": "Sprinter TX TopGate E1",
    "Linux": "Linux Server"
  },
  "config_map": {
    "Huawei S6320-54C-EI-48S-AC": {
      "interface_key": "s6320_interfaces",
      "interface_list_key": "interface_list_50p",
      "ddm": True,
      "adsl": False,
      "fibers": 28
    },
    "Huawei S5320-36C-EI-28S-AC": {
      "interface_key": "s5320_36c_interfaces",
      "interface_list_key": "interface_list_36p",
      "ddm": True,
      "adsl": False,
      "fibers": 0
    },
    "Huawei S2350-28TP-EI-AC": {
      "interface_key": "s5320_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 0
    },
    "Huawei S2320-28TP-EI-AC": {
      "interface_key": "s5320_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 0
    },
    "Huawei S5320-28TP-LI-AC": {
      "interface_key": "s5320_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 0
    },
    "Huawei S5320-28P-LI-AC": {
      "interface_key": "s5320_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 0
    },
    "Huawei S2700-18TP-SI-AC": {
      "interface_key": "s2700_interfaces",
      "interface_list_key": "interface_list_huawei2700",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "Huawei SmartAX MA5616": {
      "interface_key": "s2700_interfaces",
      "interface_list_key": "interface_list_huawei2700",
      "ddm": False,
      "adsl": True,
      "fibers": 2
    },
    "Tp-Link TL-1600G-52PS": {
      "interface_key": "tplink_interfaces52",
      "interface_list_key": "interface_list_TL_1600G",
      "ddm": True,
      "adsl": False,
      "fibers": 0
    },
    "Tp-Link T2600G-28TS": {
      "interface_key": "s5320_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 0
    },
    "Tp-Link T2700G-28TQ": {
      "interface_key": "tplink_interfaces2",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 0
    },
    "Tp-Link TL-SL2428": {
      "interface_key": "tplink_interfaces2",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "Eltex MES2324FB": {
      "interface_key": "eltex_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 28
    },
    "Eltex MES2324P": {
      "interface_key": "eltex_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 4
    },
    "Eltex MES2324F": {
      "interface_key": "eltex_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 28
    },
    "Eltex MES2324": {
      "interface_key": "eltex_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 28
    },
    "Eltex MES2428": {
      "interface_key": "mes2428_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 4
    },
    "Eltex MES3308F": {
      "interface_key": "mes3308_interfaces",
      "interface_list_key": "eltex3308_list",
      "ddm": True,
      "adsl": False,
      "fibers": 12
    },
    "Eltex MES3316F": {
      "interface_key": "mes3316_interfaces",
      "interface_list_key": "eltex3316_list",
      "ddm": True,
      "adsl": False,
      "fibers": 16
    },
    "Eltex MES3324F": {
      "interface_key": "mes3324_interfaces",
      "interface_list_key": "eltex3324_list",
      "ddm": True,
      "adsl": False,
      "fibers": 28
    },
    "D-Link DES-1210-28": {
      "interface_key": "tplink_interfaces2c",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "Dlink DGS-3620-28SC": {
      "interface_key": "eltex_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 28
    },
    "D-Link DES-3200-26": {
      "interface_key": "tplink_interfaces2c",
      "interface_list_key": "interface_list_26p",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "D-Link DES-3200-10": {
      "interface_key": "interface_list_10p",
      "interface_list_key": "interface_list_10p",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "D-Link DGS-3000-10T": {
      "interface_key": "interface_list_10p",
      "interface_list_key": "interface_list_10p",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "D-Link DGS-3000-26TC": {
      "interface_key": "interface_list_26p",
      "interface_list_key": "interface_list_26p",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "SNR S2962-24T": {
      "interface_key": "eltex_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 4
    },
    "SNR S2985G 24T": {
      "interface_key": "eltex_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 4
    },
    "SNR S2995G": {
      "interface_key": "eltex_interfaces",
      "interface_list_key": "interface_list_28p",
      "ddm": True,
      "adsl": False,
      "fibers": 28
    },
    "SNR S2985G 8T": {
      "interface_key": "eltex_interfaces",
      "interface_list_key": "interface_list_10p",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "Mikrotik CRS112": {
      "interface_key": "s2350_interfaces",
      "interface_list_key": "interface_list_12p",
      "ddm": True,
      "adsl": False,
      "fibers": 4
    },
    "Mikrotik CRS326": {
      "interface_key": "mikrotic_CRS326_26p",
      "interface_list_key": "interface_list_26p",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "Mikrotik CSS326": {
      "interface_key": "Mikrotik_CRS326_26p",
      "interface_list_key": "interface_list_26p",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "Mikrotik RB2011LS": {
      "interface_key": "RB2011LS_interface_list",
      "interface_list_key": "interface_list_11p",
      "ddm": True,
      "adsl": False,
      "fibers": 1
    },
    "Mikrotik RB760iGS": {
      "interface_key": "Mikrotik_CRS326_26p",
      "interface_list_key": "interface_list_8p",
      "ddm": True,
      "adsl": False,
      "fibers": 1
    },
    "ZyXEL IES-612": {
      "interface_key": "zyxel_interfaces_adsl_12_2",
      "interface_list_key": "interface_list_12p",
      "ddm": False,
      "adsl": True,
      "fibers": 0
    },
    "ZyXEL IES1248-51": {
      "interface_key": "zyxel_interfaces_adsl_48_2",
      "interface_list_key": "interface_list_50p",
      "ddm": False,
      "adsl": True,
      "fibers": 0
    },
    "ZYXEL SAM1008": {
      "interface_key": "zyxel_interfaces_shdsl_8_1",
      "interface_list_key": "interface_list_9p",
      "ddm": False,
      "adsl": True,
      "fibers": 0
    },
    "Cisco SG200-26": {
      "interface_key": "SG200_interface_list_26p",
      "interface_list_key": "cisco_list",
      "ddm": True,
      "adsl": False,
      "fibers": 2
    },
    "Linux Server": {
      "interface_key": "server",
      "interface_list_key": "server",
      "ddm": False,
      "adsl": False,
      "fibers": 0
    }
  }
}


# Функция для объединения словарей
def merge_data(models, config_map):
    merged_data = {}

    for short_name, full_name in models.items():
        if full_name in config_map:
            # Объединение данных из models и config_map, если конфигурация существует
            merged_data[short_name] = {"name": full_name, **config_map[full_name]}
        else:
            # Если конфигурации нет, добавляем только имя
            merged_data[short_name] = {"name": full_name}

    return merged_data


# Объединяем данные
merged_result = merge_data(data["models"], data["config_map"])

# Сохраняем в JSON
with open("merged_data.json", "w", encoding="utf-8") as file:
    json.dump(merged_result, file, ensure_ascii=False, indent=2)

print("Объединенные данные сохранены в merged_data.json")


if __name__ == "__main__":
    # Объединяем данные
    merged_result = merge_data(data["models"], data["config_map"])

    # Сохраняем в JSON
    with open("merged_data.json", "w", encoding="utf-8") as file:
        json.dump(merged_result, file, ensure_ascii=False, indent=2)

    print("Объединенные данные сохранены в merged_data.json")