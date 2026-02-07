import tkinter as tk
from tkinter import ttk, messagebox
import math
import threading
import time
from queue import Queue

class StepperMotorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление шаговым двигателем")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Переменные управления
        self.motor_running = False
        self.current_position = 0
        self.target_position = 0
        self.motor_speed = 10  # шагов в секунду
        self.motor_direction = 1  # 1 - вперед, -1 - назад
        self.step_mode = 1  # Режим шага (1, 1/2, 1/4, 1/8)
        self.motor_queue = Queue()
        
        # Цветовая схема
        self.bg_color = "#2b2b2b"
        self.frame_bg = "#3c3f41"
        self.btn_color = "#5c6162"
        self.btn_active = "#4a9c82"
        self.text_color = "#ffffff"
        self.motor_color = "#4a9c82"
        self.axis_color = "#555555"
        
        self.root.configure(bg=self.bg_color)
        
        # Создание интерфейса
        self.create_widgets()
        
        # Запуск потока для анимации двигателя
        self.animation_thread = threading.Thread(target=self.motor_animation_loop, daemon=True)
        self.animation_thread.start()
        
        # Запуск обработки команд двигателя
        self.process_motor_commands()

    def create_widgets(self):
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель управления
        control_frame = tk.Frame(main_frame, bg=self.frame_bg, relief=tk.RAISED, bd=2)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Заголовок управления
        control_label = tk.Label(control_frame, text="Управление двигателем", 
                                 font=("Arial", 16, "bold"), bg=self.frame_bg, fg=self.text_color)
        control_label.pack(pady=10)
        
        # Управление направлением
        direction_frame = tk.LabelFrame(control_frame, text="Направление вращения", 
                                        font=("Arial", 12), bg=self.frame_bg, fg=self.text_color)
        direction_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.direction_var = tk.StringVar(value="Вперед")
        
        forward_btn = tk.Radiobutton(direction_frame, text="Вперед (по часовой)", variable=self.direction_var,
                                     value="Вперед", font=("Arial", 10), bg=self.frame_bg, fg=self.text_color,
                                     selectcolor=self.btn_color, command=self.update_direction)
        forward_btn.pack(anchor=tk.W, padx=10, pady=5)
        
        backward_btn = tk.Radiobutton(direction_frame, text="Назад (против часовой)", variable=self.direction_var,
                                      value="Назад", font=("Arial", 10), bg=self.frame_bg, fg=self.text_color,
                                      selectcolor=self.btn_color, command=self.update_direction)
        backward_btn.pack(anchor=tk.W, padx=10, pady=5)
        
        # Управление скоростью
        speed_frame = tk.LabelFrame(control_frame, text="Скорость вращения", 
                                    font=("Arial", 12), bg=self.frame_bg, fg=self.text_color)
        speed_frame.pack(fill=tk.X, padx=10, pady=10)
        
        speed_label = tk.Label(speed_frame, text="Шагов в секунду:", 
                               font=("Arial", 10), bg=self.frame_bg, fg=self.text_color)
        speed_label.pack(anchor=tk.W, padx=10, pady=5)
        
        self.speed_scale = tk.Scale(speed_frame, from_=1, to=100, orient=tk.HORIZONTAL, 
                                    length=200, bg=self.frame_bg, fg=self.text_color,
                                    troughcolor=self.btn_color, highlightbackground=self.frame_bg,
                                    command=self.update_speed)
        self.speed_scale.set(self.motor_speed)
        self.speed_scale.pack(padx=10, pady=5)
        
        # Режим шага
        step_frame = tk.LabelFrame(control_frame, text="Режим шага", 
                                   font=("Arial", 12), bg=self.frame_bg, fg=self.text_color)
        step_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.step_var = tk.StringVar(value="Полный шаг")
        
        step_modes = [("Полный шаг (1)", "Полный шаг"),
                      ("Полушаг (1/2)", "Полушаг"),
                      ("Четверть шага (1/4)", "Четверть шага"),
                      ("Восьмая шага (1/8)", "Восьмая шага")]
        
        for text, mode in step_modes:
            step_btn = tk.Radiobutton(step_frame, text=text, variable=self.step_var,
                                     value=mode, font=("Arial", 10), bg=self.frame_bg, fg=self.text_color,
                                     selectcolor=self.btn_color, command=self.update_step_mode)
            step_btn.pack(anchor=tk.W, padx=10, pady=2)
        
        # Управление позицией
        position_frame = tk.LabelFrame(control_frame, text="Позиционирование", 
                                       font=("Arial", 12), bg=self.frame_bg, fg=self.text_color)
        position_frame.pack(fill=tk.X, padx=10, pady=10)
        
        pos_label = tk.Label(position_frame, text="Целевая позиция (шагов):", 
                             font=("Arial", 10), bg=self.frame_bg, fg=self.text_color)
        pos_label.pack(anchor=tk.W, padx=10, pady=5)
        
        self.position_entry = tk.Entry(position_frame, font=("Arial", 12), bg=self.btn_color, fg=self.text_color,
                                       insertbackground=self.text_color, relief=tk.FLAT)
        self.position_entry.pack(fill=tk.X, padx=10, pady=5)
        self.position_entry.insert(0, "0")
        
        move_btn = tk.Button(position_frame, text="Переместить в позицию", font=("Arial", 11),
                             bg=self.btn_color, fg=self.text_color, activebackground=self.btn_active,
                             command=self.move_to_position)
        move_btn.pack(pady=10)
        
        # Кнопки управления
        button_frame = tk.Frame(control_frame, bg=self.frame_bg)
        button_frame.pack(fill=tk.X, padx=10, pady=20)
        
        self.start_btn = tk.Button(button_frame, text="СТАРТ", font=("Arial", 12, "bold"),
                                   bg=self.btn_active, fg=self.text_color, width=10,
                                   activebackground=self.btn_active, command=self.start_motor)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="СТОП", font=("Arial", 12, "bold"),
                                  bg="#c74e4e", fg=self.text_color, width=10,
                                  activebackground="#a83c3c", command=self.stop_motor)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(button_frame, text="СБРОС", font=("Arial", 12),
                              bg=self.btn_color, fg=self.text_color, width=10,
                              activebackground=self.btn_active, command=self.reset_motor)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Информационная панель
        info_frame = tk.LabelFrame(control_frame, text="Информация о двигателе", 
                                   font=("Arial", 12), bg=self.frame_bg, fg=self.text_color)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.position_label = tk.Label(info_frame, text="Текущая позиция: 0 шагов", 
                                       font=("Arial", 10), bg=self.frame_bg, fg=self.text_color)
        self.position_label.pack(anchor=tk.W, padx=10, pady=5)
        
        self.speed_label = tk.Label(info_frame, text="Текущая скорость: 10 шаг/сек", 
                                    font=("Arial", 10), bg=self.frame_bg, fg=self.text_color)
        self.speed_label.pack(anchor=tk.W, padx=10, pady=5)
        
        self.mode_label = tk.Label(info_frame, text="Режим шага: Полный шаг", 
                                   font=("Arial", 10), bg=self.frame_bg, fg=self.text_color)
        self.mode_label.pack(anchor=tk.W, padx=10, pady=5)
        
        self.status_label = tk.Label(info_frame, text="Статус: Остановлен", 
                                     font=("Arial", 10), bg=self.frame_bg, fg="#c74e4e")
        self.status_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # Правая панель с анимацией
        animation_frame = tk.Frame(main_frame, bg=self.bg_color)
        animation_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Заголовок анимации
        animation_label = tk.Label(animation_frame, text="Анимация шагового двигателя", 
                                   font=("Arial", 16, "bold"), bg=self.bg_color, fg=self.text_color)
        animation_label.pack(pady=10)
        
        # Холст для анимации двигателя
        self.canvas = tk.Canvas(animation_frame, width=500, height=500, bg=self.bg_color, 
                                highlightthickness=0, relief=tk.FLAT)
        self.canvas.pack(pady=10)
        
        # Создание элементов анимации
        self.create_motor_animation()
        
        # График позиции
        plot_frame = tk.LabelFrame(animation_frame, text="График позиции", 
                                   font=("Arial", 12), bg=self.bg_color, fg=self.text_color)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.plot_canvas = tk.Canvas(plot_frame, width=500, height=150, bg=self.frame_bg, 
                                     highlightthickness=0, relief=tk.FLAT)
        self.plot_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Данные для графика
        self.position_history = [0] * 50
        self.draw_position_plot()

    def create_motor_animation(self):
        # Очистка холста
        self.canvas.delete("all")
        
        # Координаты центра
        self.center_x = 250
        self.center_y = 250
        self.radius = 120
        
        # Ротор двигателя (внешний круг)
        self.canvas.create_oval(
            self.center_x - self.radius,
            self.center_y - self.radius,
            self.center_x + self.radius,
            self.center_y + self.radius,
            outline=self.axis_color,
            width=3,
            fill=self.bg_color
        )
        
        # Внутренний круг
        inner_radius = self.radius - 20
        self.canvas.create_oval(
            self.center_x - inner_radius,
            self.center_y - inner_radius,
            self.center_x + inner_radius,
            self.center_y + inner_radius,
            outline=self.axis_color,
            width=2,
            fill=self.bg_color
        )
        
        # Ось вращения
        self.canvas.create_oval(
            self.center_x - 10,
            self.center_y - 10,
            self.center_x + 10,
            self.center_y + 10,
            fill=self.axis_color,
            outline=self.axis_color
        )
        
        # Создание магнитных полюсов (статор)
        pole_length = self.radius - 30
        for i in range(4):
            angle = i * (math.pi / 2)
            x1 = self.center_x + math.cos(angle) * 30
            y1 = self.center_y + math.sin(angle) * 30
            x2 = self.center_x + math.cos(angle) * pole_length
            y2 = self.center_y + math.sin(angle) * pole_length
            
            # Магнитные полюса статора
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill="#6d6d6d",
                width=12,
                capstyle=tk.ROUND
            )
            
            # Обозначение полюсов (N/S)
            label_x = self.center_x + math.cos(angle) * (pole_length + 20)
            label_y = self.center_y + math.sin(angle) * (pole_length + 20)
            
            pole_label = "N" if i % 2 == 0 else "S"
            self.canvas.create_text(
                label_x, label_y,
                text=pole_label,
                fill=self.text_color,
                font=("Arial", 12, "bold")
            )
        
        # Создание ротора (подвижная часть)
        self.rotor_lines = []
        rotor_line_count = 8
        rotor_angle_offset = 0
        
        for i in range(rotor_line_count):
            angle = rotor_angle_offset + i * (2 * math.pi / rotor_line_count)
            x1 = self.center_x + math.cos(angle) * 20
            y1 = self.center_y + math.sin(angle) * 20
            x2 = self.center_x + math.cos(angle) * (self.radius - 40)
            y2 = self.center_y + math.sin(angle) * (self.radius - 40)
            
            line = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=self.motor_color,
                width=6,
                capstyle=tk.ROUND
            )
            self.rotor_lines.append(line)
        
        # Текстовая информация на анимации
        self.canvas.create_text(
            self.center_x, self.center_y,
            text="ШАГОВЫЙ\nДВИГАТЕЛЬ",
            fill=self.text_color,
            font=("Arial", 12, "bold"),
            justify=tk.CENTER
        )
        
        # Отображение текущего угла
        self.angle_text = self.canvas.create_text(
            self.center_x, self.center_y + 180,
            text="Угол: 0°",
            fill=self.text_color,
            font=("Arial", 10)
        )
        
        # Индикатор направления
        self.direction_indicator = self.canvas.create_oval(
            self.center_x - 180, self.center_y - 180,
            self.center_x - 150, self.center_y - 150,
            fill="#c74e4e",  # Красный - остановлен
            outline=self.axis_color,
            width=2
        )
        
        self.canvas.create_text(
            self.center_x - 165, self.center_y - 190,
            text="Направление",
            fill=self.text_color,
            font=("Arial", 8)
        )

    def draw_position_plot(self):
        # Очистка холста графика
        self.plot_canvas.delete("all")
        
        width = self.plot_canvas.winfo_width()
        height = self.plot_canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Рисование осей
        self.plot_canvas.create_line(30, height-30, width-30, height-30, fill=self.axis_color, width=2)  # X-axis
        self.plot_canvas.create_line(30, 30, 30, height-30, fill=self.axis_color, width=2)  # Y-axis
        
        # Подписи осей
        self.plot_canvas.create_text(15, height//2, text="Позиция", fill=self.text_color, font=("Arial", 10), angle=90)
        self.plot_canvas.create_text(width//2, height-15, text="Время (шаги)", fill=self.text_color, font=("Arial", 10))
        
        # Масштабирование данных для графика
        max_val = max(self.position_history) if max(self.position_history) > 0 else 1
        min_val = min(self.position_history)
        range_val = max_val - min_val if max_val != min_val else 1
        
        plot_height = height - 60
        plot_width = width - 60
        
        # Рисование графика
        points = []
        for i, value in enumerate(self.position_history):
            x = 30 + (i / (len(self.position_history) - 1)) * plot_width if len(self.position_history) > 1 else 30
            y = height - 30 - ((value - min_val) / range_val) * plot_height
            points.append((x, y))
        
        # Соединение точек
        if len(points) > 1:
            for i in range(len(points) - 1):
                self.plot_canvas.create_line(points[i][0], points[i][1], 
                                            points[i+1][0], points[i+1][1], 
                                            fill=self.motor_color, width=2)
        
        # Рисование точек
        for x, y in points:
            self.plot_canvas.create_oval(x-3, y-3, x+3, y+3, fill=self.motor_color, outline=self.motor_color)
        
        # Текущее значение
        if self.position_history:
            current_value = self.position_history[-1]
            self.plot_canvas.create_text(width-50, 20, 
                                         text=f"Текущ.: {current_value}", 
                                         fill=self.text_color, font=("Arial", 10))

    def update_direction(self):
        direction = self.direction_var.get()
        if direction == "Вперед":
            self.motor_direction = 1
            self.canvas.itemconfig(self.direction_indicator, fill="#4a9c82")  # Зеленый
        else:
            self.motor_direction = -1
            self.canvas.itemconfig(self.direction_indicator, fill="#4a6b9c")  # Синий

    def update_speed(self, value):
        self.motor_speed = int(value)
        self.speed_label.config(text=f"Текущая скорость: {self.motor_speed} шаг/сек")

    def update_step_mode(self):
        mode = self.step_var.get()
        if mode == "Полный шаг":
            self.step_mode = 1
        elif mode == "Полушаг":
            self.step_mode = 0.5
        elif mode == "Четверть шага":
            self.step_mode = 0.25
        else:  # Восьмая шага
            self.step_mode = 0.125
        
        self.mode_label.config(text=f"Режим шага: {mode}")

    def move_to_position(self):
        try:
            self.target_position = int(self.position_entry.get())
            self.motor_queue.put(("move_to", self.target_position))
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число для позиции")

    def start_motor(self):
        if not self.motor_running:
            self.motor_running = True
            self.motor_queue.put(("start",))
            self.status_label.config(text="Статус: Запущен", fg="#4a9c82")
            self.start_btn.config(state=tk.DISABLED)

    def stop_motor(self):
        if self.motor_running:
            self.motor_running = False
            self.motor_queue.put(("stop",))
            self.status_label.config(text="Статус: Остановлен", fg="#c74e4e")
            self.start_btn.config(state=tk.NORMAL)
            self.canvas.itemconfig(self.direction_indicator, fill="#c74e4e")  # Красный

    def reset_motor(self):
        self.current_position = 0
        self.target_position = 0
        self.position_entry.delete(0, tk.END)
        self.position_entry.insert(0, "0")
        self.position_label.config(text="Текущая позиция: 0 шагов")
        self.position_history = [0] * 50
        self.draw_position_plot()
        self.update_motor_visualization()

    def update_motor_visualization(self):
        # Обновление угла поворота ротора
        angle_deg = self.current_position % 360
        
        # Поворот линий ротора
        rotor_angle_offset = math.radians(angle_deg)
        rotor_line_count = len(self.rotor_lines)
        
        for i, line in enumerate(self.rotor_lines):
            angle = rotor_angle_offset + i * (2 * math.pi / rotor_line_count)
            x1 = self.center_x + math.cos(angle) * 20
            y1 = self.center_y + math.sin(angle) * 20
            x2 = self.center_x + math.cos(angle) * (self.radius - 40)
            y2 = self.center_y + math.sin(angle) * (self.radius - 40)
            
            self.canvas.coords(line, x1, y1, x2, y2)
        
        # Обновление текста угла
        self.canvas.itemconfig(self.angle_text, text=f"Угол: {angle_deg:.1f}°")
        
        # Обновление позиции на графике
        self.position_history.pop(0)
        self.position_history.append(self.current_position)
        
        # Обновление информационных меток
        self.position_label.config(text=f"Текущая позиция: {self.current_position} шагов")
        
        # Перерисовка графика
        self.draw_position_plot()

    def motor_animation_loop(self):
        step_counter = 0
        last_update_time = time.time()
        
        while True:
            current_time = time.time()
            elapsed = current_time - last_update_time
            
            if self.motor_running and elapsed >= (1.0 / self.motor_speed):
                # Выполнение шага
                step_value = self.step_mode * self.motor_direction
                self.current_position += step_value
                
                # Обновление визуализации
                self.root.after(0, self.update_motor_visualization)
                
                last_update_time = current_time
                step_counter += 1
            
            # Небольшая задержка для снижения нагрузки на ЦП
            time.sleep(0.01)

    def process_motor_commands(self):
        # Обработка команд из очереди
        try:
            while not self.motor_queue.empty():
                command = self.motor_queue.get_nowait()
                
                if command[0] == "start":
                    self.motor_running = True
                    self.status_label.config(text="Статус: Запущен", fg="#4a9c82")
                    self.start_btn.config(state=tk.DISABLED)
                    
                elif command[0] == "stop":
                    self.motor_running = False
                    self.status_label.config(text="Статус: Остановлен", fg="#c74e4e")
                    self.start_btn.config(state=tk.NORMAL)
                    
                elif command[0] == "move_to":
                    self.target_position = command[1]
                    # Просто обновляем целевую позицию, двигатель продолжит движение
                    
        except:
            pass
        
        # Планируем следующую проверку очереди
        self.root.after(100, self.process_motor_commands)

def main():
    root = tk.Tk()
    app = StepperMotorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
