        $(document).ready(function () {
            // Инициализация кнопок
            $(".menu-item").button();
            $(".delete-button").button({
                icon: "ui-icon-trash",
                showLabel: true
            });
            $(".completed-button").button({
                icon: "ui-icon-check",
                showLabel: true
            });
            // Преобразование кнопок в виджеты jQuery UI
    $(".grant-admin-button").button({
        icon: "ui-icon-plus",
        showLabel: true
    });

    $(".revoke-admin-button").button({
        icon: "ui-icon-minus",
        showLabel: true
    });

            // Инициализация tooltip
            $(document).tooltip({
                track: true
            });

            // Автоперезагрузка страницы каждые 10 секунд
            setInterval(() => {
                window.location.reload();
            }, 10000);
        });
function deleteUser(tg_id) {
    if (confirm("Are you sure you want to delete this user?")) {
        $.ajax({
            url: `/admin/users/${tg_id}`,
            method: "DELETE",
            success: function (response) {
                showNotification(response.message || "User deleted successfully");
                updateUsersTable();
            },
            error: function (xhr) {
                showNotification("Error: " + xhr.responseText, true);
            }
        });
    }
}
        function sendAjax(url, action, tg_id) {
            const data = { action };
            if (tg_id) data['tg_id'] = tg_id;

            $.ajax({
                url,
                method: "POST",
                data,
                success: function (response) {
                    showNotification(response.message || "Action completed successfully", "success");
                    if (["grant_admin", "revoke_admin"].includes(action)) {
                        updateUsersTable();
                    }
                },
                error: function (xhr) {
                    showNotification("Error: " + xhr.responseText, "error");
                }
            });
        }

        function showNotification(message, type = "success") {
            const notification = $("#notification");
            notification
                .text(message)
                .removeClass("success error")
                .addClass(type)
                .fadeIn();
            setTimeout(() => notification.fadeOut(), 3000);
        }

function updateUsersTable() {
    $.ajax({
        url: "/admin/users",
        method: "GET",
        success: function (html) {
            $("#users-table-container").html(html);
        },
        error: function (xhr) {
            showNotification("Failed to update users table", true);
        }
    });
}
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("th").forEach(headerCell => {
        // Добавляем контейнер для иконки в каждый заголовок
        headerCell.innerHTML += ' <span class="sort-icon">⬍</span>';

        headerCell.addEventListener("click", () => {
            const table = headerCell.closest("table");
            const columnIndex = Array.from(headerCell.parentNode.children).indexOf(headerCell);

            // Удаляем иконки из всех заголовков
            table.querySelectorAll("th .sort-icon").forEach(icon => icon.textContent = "⬍");

            // Выполняем сортировку
            sortTable(table, columnIndex, headerCell);
        });
    });
});

function sortTable(table, columnIndex, headerCell) {
    const rows = Array.from(table.rows).slice(1); // Пропускаем заголовок таблицы
    const isAscending = table.dataset.sortOrder === "asc";

    // Определение типа данных для сортировки
    const getCellValue = (row, index) => row.cells[index]?.innerText.trim();
    const isNumericColumn = rows.every(row => !isNaN(parseFloat(getCellValue(row, columnIndex))));
    const isDateColumn = rows.every(row => !isNaN(Date.parse(getCellValue(row, columnIndex))));

    rows.sort((rowA, rowB) => {
        let cellA = getCellValue(rowA, columnIndex);
        let cellB = getCellValue(rowB, columnIndex);

        if (isNumericColumn) {
            return isAscending
                ? parseFloat(cellA) - parseFloat(cellB)
                : parseFloat(cellB) - parseFloat(cellA);
        } else if (isDateColumn) {
            return isAscending
                ? new Date(cellA) - new Date(cellB)
                : new Date(cellB) - new Date(cellA);
        } else {
            return isAscending
                ? cellA.localeCompare(cellB)
                : cellB.localeCompare(cellA);
        }
    });

    rows.forEach(row => table.tBodies[0].appendChild(row));

    // Обновляем иконку для текущего заголовка
    const sortIcon = headerCell.querySelector(".sort-icon");
    sortIcon.textContent = isAscending ? "▲" : "▼";

    // Переключение порядка сортировки
    table.dataset.sortOrder = isAscending ? "desc" : "asc";
}
