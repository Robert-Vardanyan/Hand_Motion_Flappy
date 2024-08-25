import cv2
import mediapipe as mp
import numpy as np
import random
import pygame
from pygame.locals import *


# Инициализация Pygame
pygame.init()

# Размеры экрана игры
game_width, game_height = 800, 600

# Создаем окно Pygame
screen = pygame.display.set_mode((game_width, game_height))

# Установка иконки и заголовка окна
icon = pygame.image.load(r'gallery\icon.png')
pygame.display.set_icon(icon)
pygame.display.set_caption('Flappy Bird by ROVA')

# Установка кадровой частоты
clock = pygame.time.Clock()

# Инициализация шрифта для отображения счета
score_font = pygame.font.Font('PressStart2P-Regular.ttf', 30)

# Инициализация MediaPipe Hand для распознавания жестов руками
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Захват видео с веб-камеры
cap = cv2.VideoCapture(0)

# Flappy Bird настройки
SCORE = 0
SCREEN_WIDHT = 400
SCREEN_HEIGHT = 600
SPEED = 15
GRAVITY = 2.5
GAME_SPEED = 10
GROUND_WIDHT = 2 * SCREEN_WIDHT
GROUND_HEIGHT = 100
PIPE_WIDHT = 80
PIPE_HEIGHT = 500
PIPE_GAP = 150


# Класс Bird представляет игровую птицу
class Bird(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.images = [pygame.image.load(r'gallery\yellowbird-upflap.png').convert_alpha(),
                       pygame.image.load(r'gallery\yellowbird-midflap.png').convert_alpha(),
                       pygame.image.load(r'gallery\yellowbird-downflap.png').convert_alpha()]
        self.speed = SPEED
        self.current_image = 0
        self.image = pygame.image.load(r'gallery\yellowbird-upflap.png').convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDHT + 400  / 6
        self.rect[1] = SCREEN_HEIGHT / 2

    # Метод для обновления состояния птицы
    def update(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]
        self.speed += GRAVITY
        self.rect[1] += self.speed

    # Метод для прыжка птицы
    def bump(self):
        self.speed = -SPEED

    # Метод для начальной анимации птицы
    def begin(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]


# Класс Pipe представляет трубу, через которую должна пролетать птица
class Pipe(pygame.sprite.Sprite):
    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('gallery/pipe-green.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDHT, PIPE_HEIGHT))
        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        if inverted:
            self.rect[1] = - (self.rect[3] - ysize)
        else:
            self.rect[1] = game_height - ysize
        self.mask = pygame.mask.from_surface(self.image)
        self.passed = False

    # Метод для обновления положения трубы
    def update(self):
        self.rect[0] -= GAME_SPEED


# Класс Ground представляет землю внизу экрана
class Ground(pygame.sprite.Sprite):
    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('gallery/base.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDHT, GROUND_HEIGHT))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT

    # Метод для обновления положения земли
    def update(self):
        self.rect[0] -= GAME_SPEED


# Проверка выхода спрайта за пределы экрана
def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2]) 


# Генерация новых труб
def get_random_pipes(xpos):
    size = random.randint(100, 300)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted


# Сброс игры до начального состояния
def reset_game():
    global SCORE, bird_group, ground_group, pipe_group, bird, game_over, begin

    SCORE = 0
    bird_group.empty()
    ground_group.empty()
    pipe_group.empty()

    bird = Bird()
    bird_group.add(bird)

    for i in range(2):
        ground = Ground(GROUND_WIDHT * i)
        ground_group.add(ground)

    for i in range(2):
        pipes = get_random_pipes(SCREEN_WIDHT * i + 800)
        pipe_group.add(pipes[0])
        pipe_group.add(pipes[1])

    game_over = False
    begin = True


# Инициализация игры Flappy Bird
def init_flappy_bird():
    global bird_group, ground_group, pipe_group, bird

    bird_group = pygame.sprite.Group()
    bird = Bird()
    bird_group.add(bird)

    ground_group = pygame.sprite.Group()
    for i in range(2):
        ground = Ground(GROUND_WIDHT * i)
        ground_group.add(ground)

    pipe_group = pygame.sprite.Group()
    for i in range(2):
        pipes = get_random_pipes(SCREEN_WIDHT * i + 800)
        pipe_group.add(pipes[0])
        pipe_group.add(pipes[1])
init_flappy_bird()


# Проверка столкновения с трубами
def check_collision_with_pipes(bird, pipes):
    for pipe in pipes:
        if pygame.sprite.collide_mask(bird, pipe):
            return True
    return False


# Проверка столкновения с землей
def check_collision_with_ground(bird, ground_group):
    for ground in ground_group:
        if pygame.sprite.collide_mask(bird, ground):
            return True
    return False


# Проверка прохождения птицей трубы и увеличение счета
def check_passed_pipe(bird, pipes, score):
    for pipe in pipes:
        if pipe.rect[0] + PIPE_WIDHT < bird.rect[0] and not pipe.passed:
            pipe.passed = True
            return score + 1
    return score


# Обновление экрана игры
def update_screen(image, hand_image):
    global game_over, SCORE

    # Очистка экрана
    screen.fill((0, 0, 0))

    if not game_over:
        # Обновление земли и труб
        if is_off_screen(ground_group.sprites()[0]):
            ground_group.remove(ground_group.sprites()[0])
            ground_group.add(Ground(GROUND_WIDHT - 20))

        if is_off_screen(pipe_group.sprites()[0]):
            pipe_group.remove(pipe_group.sprites()[0])
            pipe_group.remove(pipe_group.sprites()[0])
            pipes = get_random_pipes(SCREEN_WIDHT * 2)
            pipe_group.add(pipes[0])
            pipe_group.add(pipes[1])

        # Обновление счета
        SCORE = check_passed_pipe(bird, pipe_group, SCORE)  

        # Обновление всех спрайтов
        bird_group.update()
        ground_group.update()
        pipe_group.update()

        # Проверка на столкновения
        if check_collision_with_pipes(bird, pipe_group):
            game_over = True

        if check_collision_with_ground(bird, ground_group):
            game_over = True

        # Отображение фона
        screen.blit(pygame.transform.scale(pygame.image.load('gallery/background-day.png'), (game_width - 400, game_height)), (400, 0))
        bird_group.draw(screen)
        pipe_group.draw(screen)
        ground_group.draw(screen)

        # Отображение счета
        score_int = score_font.render(f'{SCORE}', True, (255, 255, 255))
        rect_score = pygame.Rect(400, 0, 400, 60)
        r_score = score_int.get_rect(center=rect_score.center)
        screen.blit(score_int, r_score)

    # Отображение видео с камеры
    screen.blit(image, (0, 0))
    screen.blit(hand_image, (0, 300))


# Основная функция игры
def main():
    global running, begin, game_over, SCORE, gesture_detected

    running = True
    begin = True
    game_over = False
    gesture_detected = False
    
    score_font = pygame.font.Font('PressStart2P-Regular.ttf', 30)

    # Использование MediaPipe для распознавания жестов
    with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if (event.type == pygame.KEYDOWN and (event.key == pygame.K_SPACE or event.key == pygame.K_UP)) or (gesture_detected and game_over):
                    if game_over:
                        reset_game()
                    else:
                        bird.bump()
                        if begin:
                            begin = False

            # Захват кадра с камеры
            ret, frame = cap.read()
            if not ret:
                break

            # Переводим изображение в RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Обнаружение руки и пальцев
            results = hands.process(image)

            # Переводим изображение обратно в BGR
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Создаем пустое черное изображение для отображения отметок и линий
            hand_image = np.zeros((300, 400, 3), dtype=np.uint8)

            # Обнуляем состояние жеста
            gesture_detected = False

            # Если обнаружены руки
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Рисуем отметки и линии на основном изображении
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Рисуем отметки и линии на изображении для руки
                    mp_drawing.draw_landmarks(
                        hand_image, 
                        hand_landmarks, 
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=3),
                        mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                    )

                    # Получаем координаты пальцев
                    landmarks = []
                    for id, lm in enumerate(hand_landmarks.landmark):
                        h, w, c = image.shape
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        landmarks.append((cx, cy))

                    # Проверяем касание пальцев
                    if abs(landmarks[4][0] - landmarks[8][0]) < 30 and abs(landmarks[4][1] - landmarks[8][1]) < 30:
                        gesture_detected = True

            # Меняем размер изображений для окна игры
            image = cv2.resize(image, (400, 300))
            hand_image = cv2.resize(hand_image, (400, 300))

            # Преобразуем изображения OpenCV в формат, совместимый с Pygame
            image = np.rot90(image)  # Поворот изображения для правильного отображения
            hand_image = np.rot90(hand_image)  # Поворот изображения для правильного отображения
            image = pygame.surfarray.make_surface(image)
            hand_image = pygame.surfarray.make_surface(hand_image)

            # Обновляем экран
            update_screen(image, hand_image)

            # Проверяем жесты для управления
            font = pygame.font.Font(None, 36)
            if gesture_detected:
                text = font.render('Click', True, (124,252,0))  
                if game_over:  # Перезапускаем игру, если она окончена и жест обнаружен
                    reset_game()
                else:
                    bird.bump()
                    if begin:
                        begin = False
            else:
                text = font.render('Not click', True, (255, 0, 0)) 
            screen.blit(text, (0, 0))

            # Обработка конца игры
            if game_over:
                screen.blit(pygame.transform.scale(pygame.image.load('gallery/background-day.png'), (game_width - 400, game_height)), (400, 0))

                # Отображаем счёт
                score_int = score_font.render(f'{SCORE}', True, (255, 255, 255))
                rect_score = pygame.Rect(400, 0, 400, 60)
                r_score = score_int.get_rect(center=rect_score.center)
                screen.blit(score_int, r_score)

                # Отображаем сообщение 'Game Over'
                game_over_rect = pygame.image.load('gallery/gameover.png').convert_alpha().get_rect(center=(SCREEN_WIDHT // 2 + 400, SCREEN_HEIGHT // 2))
                screen.blit(pygame.image.load('gallery/gameover.png').convert_alpha(), game_over_rect)

            pygame.display.update()
            clock.tick(30)

    cap.release()
    pygame.quit()


# Запуск основной функции
main()
