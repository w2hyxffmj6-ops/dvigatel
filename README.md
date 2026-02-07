# Приложение для управления шаговым двигателем

## Обзор архитектуры

### Основной класс приложения

```python
class StepperMotorApp:
    def __init__(self, root):
        # Инициализация главного окна Tkinter
        self.root = root
        self.root.title("Управление шаговым двигателем")
        
        # Состояние двигателя
        self.motor_running = False
        self.current_position = 0
        self.motor_speed = 10
        
        # Создание интерфейса
        self.create_widgets()
        
        # Запуск потоков
        self.animation_thread = threading.Thread(
            target=self.motor_animation_loop, 
            daemon=True
        )
        self.animation_thread.start()
```

### Компоненты интерфейса

**Панель управления создается методом:**
```python
def create_widgets(self):
    # Основные фреймы
    control_frame = tk.Frame(main_frame, bg=self.frame_bg)
    control_frame.pack(side=tk.LEFT, fill=tk.Y)
    
    # Элементы управления
    self.speed_scale = tk.Scale(
        speed_frame, 
        from_=1, 
        to=100, 
        orient=tk.HORIZONTAL,
        command=self.update_speed
    )
    
    # Кнопки управления
    self.start_btn = tk.Button(
        button_frame, 
        text="СТАРТ",
        command=self.start_motor
    )
```

**Визуализация двигателя:**
```python
def create_motor_animation(self):
    # Рисование статора (неподвижной части)
    self.canvas.create_oval(
        self.center_x - self.radius,
        self.center_y - self.radius,
        self.center_x + self.radius,
        self.center_y + self.radius,
        outline=self.axis_color,
        width=3
    )
    
    # Создание ротора (вращающейся части)
    self.rotor_lines = []
    for i in range(8):
        line = self.canvas.create_line(...)
        self.rotor_lines.append(line)
```

### Управление двигателем

**Запуск и остановка:**
```python
def start_motor(self):
    if not self.motor_running:
        self.motor_running = True
        self.motor_queue.put(("start",))
        self.update_status("Запущен", "green")

def stop_motor(self):
    if self.motor_running:
        self.motor_running = False
        self.motor_queue.put(("stop",))
        self.update_status("Остановлен", "red")
```

**Основной цикл анимации:**
```python
def motor_animation_loop(self):
    while True:
        if self.motor_running:
            # Расчет нового положения
            step_value = self.step_mode * self.motor_direction
            self.current_position += step_value
            
            # Обновление интерфейса в основном потоке
            self.root.after(0, self.update_motor_visualization)
            
            # Контроль скорости
            time.sleep(1.0 / self.motor_speed)
```

### Обновление визуализации

```python
def update_motor_visualization(self):
    # Расчет угла поворота
    angle_deg = self.current_position % 360
    rotor_angle_offset = math.radians(angle_deg)
    
    # Обновление линий ротора
    for i, line in enumerate(self.rotor_lines):
        angle = rotor_angle_offset + i * (2 * math.pi / 8)
        x1 = self.center_x + math.cos(angle) * 20
        y1 = self.center_y + math.sin(angle) * 20
        x2 = self.center_x + math.cos(angle) * (self.radius - 40)
        y2 = self.center_y + math.sin(angle) * (self.radius - 40)
        
        self.canvas.coords(line, x1, y1, x2, y2)
    
    # Обновление информационных меток
    self.position_label.config(
        text=f"Текущая позиция: {self.current_position} шагов"
    )
```

### Система очередей для многопоточности

```python
def process_motor_commands(self):
    # Обработка команд из очереди
    try:
        while not self.motor_queue.empty():
            command = self.motor_queue.get_nowait()
            
            if command[0] == "start":
                # Обработка команды запуска
                self.handle_start_command()
                
            elif command[0] == "move_to":
                # Обработка команды перемещения
                self.handle_move_command(command[1])
                
    except Exception as e:
        print(f"Ошибка обработки команд: {e}")
    
    # Планирование следующей проверки
    self.root.after(100, self.process_motor_commands)
```

### График позиции

```python
def draw_position_plot(self):
    # Очистка холста
    self.plot_canvas.delete("all")
    
    # Рисование осей
    self.plot_canvas.create_line(30, height-30, width-30, height-30, ...)
    self.plot_canvas.create_line(30, 30, 30, height-30, ...)
    
    # Расчет точек графика
    points = []
    for i, value in enumerate(self.position_history):
        x = 30 + (i / len(self.position_history)) * plot_width
        y = height - 30 - ((value - min_val) / range_val) * plot_height
        points.append((x, y))
    
    # Соединение точек линией
    for i in range(len(points) - 1):
        self.plot_canvas.create_line(
            points[i][0], points[i][1], 
            points[i+1][0], points[i+1][1], 
            fill=self.motor_color, 
            width=2
        )
```

### Режимы шага

```python
def update_step_mode(self):
    mode = self.step_var.get()
    
    # Преобразование текстового значения в числовой коэффициент
    if mode == "Полный шаг":
        self.step_mode = 1.0
    elif mode == "Полушаг":
        self.step_mode = 0.5
    elif mode == "Четверть шага":
        self.step_mode = 0.25
    elif mode == "Восьмая шага":
        self.step_mode = 0.125
    
    # Обновление отображения
    self.mode_label.config(text=f"Режим шага: {mode}")
```

### Запуск приложения

```python
def main():
    # Создание корневого окна
    root = tk.Tk()
    
    # Создание экземпляра приложения
    app = StepperMotorApp(root)
    
    # Запуск главного цикла
    root.mainloop()

if __name__ == "__main__":
    main()
```

## Ключевые особенности реализации

### 1. Многопоточная архитектура
- Основной поток: GUI и обработка событий
- Отдельный поток: анимация двигателя
- Очередь команд для межпоточного взаимодействия

### 2. Объектно-ориентированный дизайн
- Инкапсуляция состояния двигателя
- Отдельные методы для каждой функции
- Четкое разделение ответственности

### 3. Анимация на основе математических расчетов
- Использование тригонометрии для вращения
- Плавное обновление координат
- Реальное время выполнения шагов

### 4. Масштабируемость
- Легко добавлять новые режимы шага
- Возможность подключения реального оборудования
- Расширяемая система визуализации

## Структура данных

### Основные переменные состояния:
```python
# Положение и движение
current_position: int      # Текущая позиция в шагах
target_position: int       # Целевая позиция
motor_speed: int          # Скорость в шагах/секунду
motor_direction: int      # Направление (1 или -1)

# Состояние системы
motor_running: bool       # Флаг работы двигателя
step_mode: float          # Коэффициент шага (1, 0.5, 0.25, 0.125)

# Визуализация
position_history: List[int]  # История позиций для графика
rotor_lines: List[int]       # Идентификаторы линий ротора на холсте
```

## Математические основы

### Расчет угла поворота:
```python
# Преобразование шагов в градусы
angle_degrees = (current_position * 360) / steps_per_revolution

# Преобразование в радианы для вычислений
angle_radians = math.radians(angle_degrees)

# Расчет координат точки на окружности
x = center_x + radius * math.cos(angle_radians)
y = center_y + radius * math.sin(angle_radians)
```

### Управление скоростью:
```python
# Интервал между шагами в секундах
step_interval = 1.0 / motor_speed

# Время ожидания в цикле анимации
time.sleep(step_interval)
```

## Рекомендации по использованию

### Для образовательных целей:
1. Изучите метод `motor_animation_loop` для понимания временных интервалов
2. Проанализируйте `update_motor_visualization` для работы с графикой
3. Исследуйте очередь команд в `process_motor_commands`

### Для расширения функциональности:
1. Добавьте новые режимы шага в метод `update_step_mode`
2. Реализуйте ускорение/замедление в `motor_animation_loop`
3. Добавьте сохранение конфигурации через JSON

### Для интеграции с оборудованием:
1. Замените виртуальное движение на GPIO управление
2. Добавьте обработку сигналов от энкодера
3. Реализуйте обратную связь по току/напряжению
