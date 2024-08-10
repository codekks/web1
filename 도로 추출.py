# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 12:28:27 2024

@author: kokyeongssu
"""

import cv2
import numpy as np
import pygame
import time
import math
import random

# 이미지 파일 경로 설정 (raw string 사용)
image_path = r'C:\Users\고경수\OneDrive\바탕 화면\공축설\capture.png'

# np.fromfile과 cv2.imdecode를 사용하여 이미지 읽기
img_array = np.fromfile(image_path, np.uint8)  # 컴퓨터가 읽을 수 있게 numpy 배열로 변환
image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)  # 이미지를 읽어옴

# 이미지를 흑백으로 변환
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 하얀색 도로 추출 (임계값 설정)
_, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

# 윤곽선 검출
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 도로의 좌표 추출
road_coords = [contour[:, 0, :] for contour in contours]

# Pygame 초기화
pygame.init()

# 화면 크기 설정
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Traffic Simulation')

# 색상 정의
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)

# 차량 클래스
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, size_x=20, size_y=10):
        super().__init__()
        self.original_image = pygame.Surface([size_x, size_y])
        self.original_image.fill(BLUE)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.size_x = size_x
        self.size_y = size_y
        self.path = []
        self.current_index = 0
        self.moving = True
        self.angle = 0
        self.start_time = None
        self.end_time = None
        self.travel_time = None

    def update(self, traffic_lights, vehicles, intersections):
        if self.path and self.current_index < len(self.path):
            if self.start_time is None:
                self.start_time = time.time()

            next_pos = self.path[self.current_index]
            next_rect = self.rect.copy()
            next_rect.x, next_rect.y = next_pos[0], next_pos[1]

            self.moving = True
            for vehicle in vehicles:
                if vehicle != self and next_rect.colliderect(vehicle.rect.inflate(40, 40)):
                    self.moving = False
                    break

            for intersection in intersections:
                intersection_rect = pygame.Rect(intersection[0] - 20, intersection[1] - 20, 40, 40)
                if self.moving and intersection_rect.colliderect(next_rect):
                    for light in traffic_lights:
                        if light.rect.colliderect(intersection_rect):
                            current_time = time.time()
                            time_since_last_switch = current_time - light.last_switch
                            if light.state == 'red':
                                self.moving = False
                                break
                            elif light.state == 'yellow' and light.red_time - time_since_last_switch <= 1:
                                self.moving = False
                                break

            if self.moving:
                dx, dy = next_pos[0] - self.rect.x, next_pos[1] - self.rect.y
                distance = math.hypot(dx, dy)
                if distance > 0:
                    self.angle = math.degrees(math.atan2(-dy, dx))
                    self.image = pygame.transform.rotate(self.original_image, self.angle)
                    self.rect = self.image.get_rect(center=self.rect.center)
                if distance < self.speed:
                    self.rect.x, self.rect.y = next_pos
                    self.current_index += 1
                else:
                    self.rect.x += self.speed * dx / distance
                    self.rect.y += self.speed * dy / distance

        elif self.path and self.current_index >= len(self.path):
            if self.end_time is None:
                self.end_time = time.time()
                self.travel_time = self.end_time - self.start_time
                print(f"Vehicle reached destination. Travel time: {self.travel_time} seconds")

    def set_path(self, path):
        self.path = path
        self.current_index = 0
        self.start_time = None
        self.end_time = None
        self.travel_time = None

# 신호등 클래스
class TrafficLight(pygame.sprite.Sprite):
    def __init__(self, x, y, green_time, yellow_time, red_time):
        super().__init__()
        self.image = pygame.Surface([20, 20])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.green_time = green_time
        self.yellow_time = yellow_time
        self.red_time = red_time
        self.state = 'red'
        self.last_switch = time.time()

    def update(self):
        current_time = time.time()
        time_since_last_switch = current_time - self.last_switch

        if self.state == 'red' and time_since_last_switch > self.red_time:
            self.state = 'green'
            self.image.fill(GREEN)
            self.last_switch = current_time
        elif self.state == 'green' and time_since_last_switch > self.green_time:
            self.state = 'yellow'
            self.image.fill(YELLOW)
            self.last_switch = current_time
        elif self.state == 'yellow' and time_since_last_switch > self.yellow_time:
            self.state = 'red'
            self.image.fill(RED)
            self.last_switch = current_time

# 도로 클래스
class Road:
    def __init__(self, start_pos, end_pos, width, color=BLACK):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.width = width
        self.color = color

    def draw(self, screen):
        pygame.draw.line(screen, self.color, self.start_pos, self.end_pos, self.width)

    def is_on_road(self, position):
        if self.start_pos[0] == self.end_pos[0]:  # Vertical road
            if self.start_pos[1] <= position[1] <= self.end_pos[1] or self.end_pos[1] <= position[1] <= self.start_pos[1]:
                if abs(position[0] - self.start_pos[0]) <= self.width // 2:
                    return True
        elif self.start_pos[1] == self.end_pos[1]:  # Horizontal road
            if self.start_pos[0] <= position[0] <= self.end_pos[0] or self.end_pos[0] <= position[0] <= self.start_pos[0]:
                if abs(position[1] - self.start_pos[1]) <= self.width // 2:
                    return True
        return False

# 차선 구분 클래스
class LaneMarker:
    def __init__(self, start_pos, end_pos, color=WHITE, style='dashed'):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.style = style

    def draw(self, screen):
        if self.style == 'dashed':
            self.draw_dashed_line(screen)

    def draw_dashed_line(self, screen):
        length = math.hypot(self.end_pos[0] - self.start_pos[0], self.end_pos[1] - self.start_pos[1])
        dash_length = 10
        dash_space = 5
        num_dashes = int(length // (dash_length + dash_space))

        for i in range(num_dashes):
            start_x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * i / num_dashes
            start_y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * i / num_dashes
            end_x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * (i + 0.5) / num_dashes
            end_y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * (i + 0.5) / num_dashes
            pygame.draw.line(screen, self.color, (start_x, start_y), (end_x, end_y), 2)

# 경로 설정 함수
def calculate_path(start_pos, end_pos, roads):
    path = [start_pos]
    current_pos = start_pos

    while current_pos != end_pos:
        if current_pos[0] != end_pos[0]:  # 수평 이동
            step = 1 if current_pos[0] < end_pos[0] else -1
            while current_pos[0] != end_pos[0]:
                current_pos = (current_pos[0] + step, current_pos[1])
                if is_road(current_pos, roads):
                    path.append(current_pos)
                else:
                    break
        if current_pos[1] != end_pos[1]:  # 수직 이동
            step = 1 if current_pos[1] < end_pos[1] else -1
            while current_pos[1] != end_pos[1]:
                current_pos = (current_pos[0], current_pos[1] + step)
                if is_road(current_pos, roads):
                    path.append(current_pos)
                else:
                    break
    return path

def is_road(position, roads):
    for road in roads:
        if road.is_on_road(position):
            return True
    return False

# 도로 객체 생성
roads = []
for road in road_coords:
    if len(road) >= 2:
        for i in range(len(road) - 1):
            start_pos = tuple(road[i])
            end_pos = tuple(road[i + 1])
            roads.append(Road(start_pos, end_pos, 40))

# 랜덤 교차로 및 신호등 생성 함수
def create_intersections_and_lights(roads):
    intersections = []
    traffic_lights = pygame.sprite.Group()
    for road1 in roads:
        for road2 in roads:
            if road1 != road2:
                if road1.start_pos[0] == road1.end_pos[0] and road2.start_pos[1] == road2.end_pos[1]:  # Vertical and horizontal
                    intersection = (road1.start_pos[0], road2.start_pos[1])
                    if 0 <= intersection[0] <= screen_width and 0 <= intersection[1] <= screen_height:
                        intersections.append(intersection)
                        light = TrafficLight(intersection[0], intersection[1], green_time=5, yellow_time=1, red_time=5)
                        traffic_lights.add(light)
                elif road1.start_pos[1] == road1.end_pos[1] and road2.start_pos[0] == road2.end_pos[0]:  # Horizontal and vertical
                    intersection = (road2.start_pos[0], road1.start_pos[1])
                    if 0 <= intersection[0] <= screen_width and 0 <= intersection[1] <= screen_height:
                        intersections.append(intersection)
                        light = TrafficLight(intersection[0], intersection[1], green_time=5, yellow_time=1, red_time=5)
                        traffic_lights.add(light)
    return intersections, traffic_lights

# 랜덤 차량 생성 함수
def create_random_vehicles(num_vehicles, roads):
    vehicles = pygame.sprite.Group()
    for _ in range(num_vehicles):
        road = random.choice(roads)
        right_side = random.choice([True, False])
        pos = random_position_on_road(road, right_side)
        speed = random.randint(1, 3)
        vehicle = Vehicle(pos[0], pos[1], speed)
        if road.start_pos[0] == road.end_pos[0]:  # Vertical road
            vehicle.angle = 0 if pos[1] < road.end_pos[1] else 180  # Set angle based on direction
        else:  # Horizontal road
            vehicle.angle = 90 if pos[0] < road.end_pos[0] else 270  # Set angle based on direction
        vehicle.image = pygame.transform.rotate(vehicle.original_image, vehicle.angle)
        vehicles.add(vehicle)
    return vehicles

# 도로 위 랜덤 위치 생성 함수
def random_position_on_road(road, right_side=True):
    if road.start_pos[0] == road.end_pos[0]:  # Vertical road
        x = road.start_pos[0] + (10 if right_side else -10)  # 중앙에서 오른쪽 또는 왼쪽
        y = random.randint(road.start_pos[1], road.end_pos[1])
        return (x, y)
    else:  # Horizontal road
        x = random.randint(road.start_pos[0], road.end_pos[0])
        y = road.start_pos[1] + (10 if right_side else -10)  # 중앙에서 위 또는 아래
        return (x, y)

# 스프라이트 그룹 생성
all_sprites = pygame.sprite.Group()
traffic_lights = pygame.sprite.Group()
'''
# 랜덤 교차로 및 신호등 생성
intersections, traffic_lights = create_intersections_and_lights(roads)
all_sprites.add(traffic_lights)

# 랜덤 차량 생성
vehicles = create_random_vehicles(5, roads)
all_sprites.add(vehicles)

# 차량 경로 설정
for vehicle in vehicles:
    start_pos = (vehicle.rect.x, vehicle.rect.y)
    start_road = next((road for road in roads if road.is_on_road(start_pos)), None)
    if start_road:
        right_side = start_pos[0] % 20 == 10 or start_pos[1] % 20 == 10
        end_pos = random_position_on_road(start_road, right_side)
        path = calculate_path(start_pos, end_pos, roads)
        print(f"Path for vehicle at ({vehicle.rect.x}, {vehicle.rect.y}): {path}")  # Debugging: Print the path
        if path:
            vehicle.set_path(path)
        else:
            print(f"No path found for vehicle at ({vehicle.rect.x}, {vehicle.rect.y})")
'''
# 메인 루프
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 업데이트
    traffic_lights.update()
    '''
    for vehicle in vehicles:
        vehicle.update(traffic_lights, vehicles, intersections)
'''
    # 화면 채우기
    screen.fill(WHITE)

    # 도로 그리기
    for road in roads:
        road.draw(screen)

    # 스프라이트 그리기
    all_sprites.draw(screen)

    # 화면 업데이트
    pygame.display.flip()

    # 초당 60 프레임으로 설정
    clock.tick(60)

pygame.quit()
