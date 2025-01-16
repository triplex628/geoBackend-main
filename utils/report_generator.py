from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from django.http import HttpResponse
from api.models import TaskModel, EmployeeTaskModel, ItemModel, EmployeeModel
from openpyxl.utils import get_column_letter
import logging
class ReportGenerator:
    def generate_task_sheet(self, sheet, employee_tasks, end_time):
        """
        Генерация листа 'Отчет по задачам', включая порядковый номер строки.
        """
        sheet.title = "Отчет по задачам"
        column_widths = [5, 30, 20, 20, 15, 20, 20, 30, 15]
        for col_num, width in enumerate(column_widths, start=1):
            sheet.column_dimensions[get_column_letter(col_num)].width = width

        headers = ["№", "Задача", "Дата постановки", "Дата завершения", "ID задачи", 
                    "Потраченное время", "Переделка", "Сотрудники", "Статус"]

        # Устанавливаем ширину колонок (добавляем ширину для первого столбца)
        
        for col_num, header in enumerate(headers, start=1):
            sheet.cell(row=1, column=col_num).value = header
            sheet.cell(row=1, column=col_num).font = Font(bold=True)
            sheet.cell(row=1, column=col_num).alignment = Alignment(horizontal="center", vertical="center")

        # Стартовая строка
        row = 2

        for task_index, task in enumerate(employee_tasks, start=1):
            # Формирование данных о задаче
            task_title = task.task.title if task.task else "Не указано"
            start_time = task.start_time.strftime("%d.%m.%Y") if task.start_time else ""
            end_time = task.end_time.strftime("%d.%m.%Y") if task.end_time else "не завершена"
            total_time = str(task.total_time) if task.total_time else "0:00:00"
            rework_time = str(task.rework_time) if task.rework_time else "0:00:00"

            # Формирование списка сотрудников и их статусов
            employees = []
            statuses = []

            for employee_task in EmployeeTaskModel.objects.filter(task=task.task):
                employee_name = f"{employee_task.employee.name} {employee_task.employee.surname}"
                employees.append(employee_name)

                # Определяем статус
                if employee_task.paused_message == "Ожидание по браку":
                    statuses.append("Закончено по браку")
                elif employee_task.paused_message == "Ожидание по комплектующим":
                    statuses.append("Закончена по недостатку комплектующих")
                elif employee_task.end_time:
                    statuses.append("Работа завершена")
                else:
                    statuses.append("В работе")

            # Заполнение строки
            sheet.cell(row=row, column=1).value = task_index  # №
            sheet.cell(row=row, column=2).value = task_title  # Задача
            sheet.cell(row=row, column=3).value = start_time  # Дата постановки
            sheet.cell(row=row, column=4).value = end_time  # Дата завершения
            sheet.cell(row=row, column=5).value = task.task.id if task.task else "N/A"  # ID задачи
            sheet.cell(row=row, column=6).value = total_time  # Потраченное время
            sheet.cell(row=row, column=7).value = rework_time  # Переделка
            sheet.cell(row=row, column=8).value = "\n".join(employees)  # Сотрудники
            sheet.cell(row=row, column=8).alignment = Alignment(wrap_text=True, vertical="top")
            sheet.cell(row=row, column=9).value = "\n".join(statuses)  # Статус
            sheet.cell(row=row, column=9).alignment = Alignment(wrap_text=True, vertical="top")

            row += 1





    def generate_equipment_sheet(self, sheet, start_time, end_time):
        """
        Генерация отчета 'По приборам' с группировкой по приборам, заданными столбцами,
        комментариями и выводом итоговой суммы продолжительности работ.
        """
        sheet.title = "По приборам"

        # Настройка логирования для отладки
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

        # Устанавливаем ширину колонок
        column_widths = [5, 15, 20, 20, 20, 30, 30, 25, 30]
        for col_num, width in enumerate(column_widths, start=1):
            sheet.column_dimensions[get_column_letter(col_num)].width = width

        # Добавляем заголовки таблицы
        headers = ["№", "ID прибора", "Дата начала работы", "Дата окончания работы", "Тип работы",
                "Продолжительность работы (общая)", "Переделка (кол-во времени)", "Сотрудник", "Комментарий"]

        try:
            # Фильтруем задачи в указанном промежутке времени
            employee_tasks = EmployeeTaskModel.objects.filter(
                start_time__gte=start_time,
                end_time__lte=end_time
            )
            logging.debug(f"Фильтрация задач успешна. Найдено {len(employee_tasks)} задач.")
        except Exception as e:
            logging.error(f"Ошибка при фильтрации задач: {e}")
            sheet.append(["Ошибка при фильтрации задач", str(e)])
            return

        # Группируем задачи по приборам
        tasks_by_item = {}
        for employee_task in employee_tasks:
            item_title = employee_task.item.title if employee_task.item else "Не указан"
            if item_title not in tasks_by_item:
                tasks_by_item[item_title] = []
            tasks_by_item[item_title].append(employee_task)

        # Стартовая строка
        row = 1

        for item_title, tasks in tasks_by_item.items():
            try:
                # Добавляем заголовок для группы задач прибора
                sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=9)
                sheet.cell(row=row, column=1).value = f"Прибор: {item_title}"
                sheet.cell(row=row, column=1).alignment = Alignment(horizontal="center", vertical="center")
                sheet.cell(row=row, column=1).font = Font(bold=True, size=14)
                row += 1

                # Добавляем заголовки таблицы
                for col_num, header in enumerate(headers, start=1):
                    sheet.cell(row=row, column=col_num).value = header
                    sheet.cell(row=row, column=col_num).font = Font(bold=True)
                    sheet.cell(row=row, column=col_num).alignment = Alignment(horizontal="center", vertical="center")
                row += 1

                # Считаем общую продолжительность работ для прибора
                total_duration_seconds = sum(
                    [et.total_time.total_seconds() if et.total_time else 0 for et in tasks],
                    0
                )
                total_duration_hours = total_duration_seconds / 3600  # Преобразуем в часы
                logging.debug(f"Общая продолжительность для '{item_title}': {total_duration_hours:.2f} ч.")

                # Заполняем строки для задач прибора
                for task_index, employee_task in enumerate(tasks, start=1):
                    task = employee_task.task
                    item = employee_task.item
                    paused_message = employee_task.paused_message
                    is_finished = task.is_available

                    # Определяем комментарий
                    if paused_message == "Ожидание по браку":
                        comment = "Закончено по браку"
                    elif paused_message == "Ожидание по комплектующим":
                        comment = "Закончена по недостатку комплектующих"
                    elif end_time:
                        comment = "Работа завершена"
                    else:
                        comment = "В работе"

                    # Вычисляем безопасное время окончания задачи
                    end_times = [et.end_time for et in tasks if et.end_time]
                    end_time_task = max(end_times) if end_times else None

                    # Заполняем строку данными
                    sheet.cell(row=row, column=1).value = task_index  # Порядковый номер
                    sheet.cell(row=row, column=2).value = item.id if item else "Не указан"  # ID прибора
                    sheet.cell(row=row, column=3).value = employee_task.start_time.strftime("%d.%m.%Y") if employee_task.start_time else ""
                    sheet.cell(row=row, column=4).value = end_time_task.strftime("%d.%m.%Y") if end_time_task else "не завершена"
                    sheet.cell(row=row, column=5).value = task.get_type_of_task_display() if hasattr(task, 'get_type_of_task_display') else task.type_of_task  # Тип работы
                    sheet.cell(row=row, column=6).value = str(employee_task.total_time)  # Общая продолжительность
                    sheet.cell(row=row, column=7).value = str(task.rework_time)  # Время на переделку
                    sheet.cell(row=row, column=8).value = f"{employee_task.employee.name} {employee_task.employee.surname}"  # Сотрудник
                    sheet.cell(row=row, column=9).value = comment  # Комментарий
                    row += 1

                # Оставляем 5 строк пустыми
                row += 5

                # Добавляем итоговую строку
                sheet.cell(row=row, column=1).value = "ИТОГ:"
                sheet.cell(row=row, column=1).font = Font(bold=True)
                sheet.cell(row=row, column=6).value = f"{total_duration_hours:.2f} ч"
                sheet.cell(row=row, column=6).font = Font(bold=True)
                row += 1

            except Exception as e:
                logging.error(f"Ошибка при обработке прибора '{item_title}': {e}")
                sheet.append([f"Ошибка при обработке прибора '{item_title}'", str(e)])
                continue







    def generate_employee_sheet(self, sheet, start_time, end_time):
        """
        Генерация третьего листа отчета с группировкой задач по сотрудникам.
        """
        sheet.title = "По сотрудникам"

        # Устанавливаем ширину колонок
        column_widths = [5, 15, 30, 20, 20, 20, 15, 20, 20]
        for col_num, width in enumerate(column_widths, start=1):
            sheet.column_dimensions[get_column_letter(col_num)].width = width

        # Заголовки задач
        headers = ["№", "ID Задачи", "Задача", "Дата взятия", "Дата окончания",
                "Потраченное время", "Переделка", "Статус работы"]
        
        # Стартовая строка
        row = 1

        # Получение всех сотрудников
        employees = EmployeeModel.objects.all()

        for employee in employees:
            # Заголовок с именем сотрудника
            sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(headers))
            sheet.cell(row=row, column=1).value = f"{employee.name} {employee.surname}"
            sheet.cell(row=row, column=1).font = Font(bold=True, size=14)
            sheet.cell(row=row, column=1).alignment = Alignment(horizontal="center", vertical="center")
            row += 1

            # Заголовок таблицы задач
            for col_num, header in enumerate(headers, start=1):
                sheet.cell(row=row, column=col_num).value = header
                sheet.cell(row=row, column=col_num).font = Font(bold=True)
                sheet.cell(row=row, column=col_num).alignment = Alignment(horizontal="center", vertical="center")
            row += 1

            # Получение всех задач для сотрудника
            employee_tasks = EmployeeTaskModel.objects.filter(
                employee=employee, start_time__gte=start_time, end_time__lte=end_time
            )

            if employee_tasks.exists():
                for task_index, task in enumerate(employee_tasks, start=1):
                    # Заполнение данных задачи
                    sheet.cell(row=row, column=1).value = task_index  # №
                    sheet.cell(row=row, column=2).value = task.task.id if task.task else "N/A"  # ID Задачи
                    sheet.cell(row=row, column=3).value = task.task.title if task.task else "N/A"  # Задача
                    sheet.cell(row=row, column=4).value = task.start_time.strftime("%d.%m.%Y") if task.start_time else "N/A"  # Дата взятия
                    sheet.cell(row=row, column=5).value = task.end_time.strftime("%d.%m.%Y") if task.end_time else "N/A"  # Дата окончания
                    sheet.cell(row=row, column=6).value = str(task.total_time) if task.total_time else "0:00:00"  # Потраченное время
                    sheet.cell(row=row, column=7).value = str(task.rework_time) if task.rework_time else "0:00:00"  # Переделка
                    sheet.cell(row=row, column=8).value = self.get_task_status(task)  # Статус работы
                    row += 1
            else:
                # Если у сотрудника нет задач
                sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(headers))
                sheet.cell(row=row, column=1).value = "Нет задач"
                sheet.cell(row=row, column=1).alignment = Alignment(horizontal="center", vertical="center")
                row += 1

            # Оставляем пустую строку между сотрудниками
            row += 1

    def get_task_status(self, task):
        """
        Получение статуса работы.
        """
        if task.paused_message == "Ожидание по браку":
            return "Закончена по браку"
        elif task.paused_message == "Ожидание по комплектующим":
            return "Закончена по недостатку комплектующих"
        elif task.end_time:
            return "Работа завершена"
        else:
            return "В работе"






    def generate_report(self, start_time, end_time):
        print(f"Генерация отчета с {start_time} по {end_time}")
        workbook = Workbook()

        # Генерация первого листа
        sheet1 = workbook.active
        self.generate_task_sheet(sheet1, EmployeeTaskModel.objects.filter(start_time__gte=start_time, end_time__lte=end_time), end_time)


        # Генерация второго листа
        sheet2 = workbook.create_sheet("По приборам")
        try:
            self.generate_equipment_sheet(sheet2, start_time, end_time)
        except Exception as e:
            print(f"Ошибка в generate_equipment_sheet: {e}")

        # Генерация третьего листа
        sheet3 = workbook.create_sheet("По сотрудникам")
        self.generate_employee_sheet(sheet3, start_time, end_time)

        # Сохранение отчета
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=full_report.xlsx'
        workbook.save(response)
        return response


