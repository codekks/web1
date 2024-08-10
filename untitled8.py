# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 11:00:23 2024

@author: kokyeongssu
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt

# 이미지 불러오기
image_path = 'C:/Users/고경수/OneDrive/바탕 화면/공축설/캡처.PNG'
image = cv2.imread(image_path)

# 이미지를 흑백으로 변환
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 하얀색 도로 추출 (임계값 설정)
_, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

# 윤곽선 검출
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 도로의 좌표 추출
road_coords = [contour[:, 0, :] for contour in contours]

# 디버깅: 첫 번째 도로 좌표 출력
if road_coords:
    print("첫 번째 도로의 좌표:", road_coords[0])
else:
    print("도로 데이터가 없습니다.")

# 결과 시각화
cv2.drawContours(image, contours, -1, (0, 255, 0), 2)
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.show()

# 도로 데이터의 좌표를 pygame 화면 크기에 맞게 변환
def transform_coordinates(coords, width, height, margin=20):
    if not coords:
        return []
    
    min_x = min([point[0] for road in coords for point in road])
    max_x = max([point[0] for road in coords for point in road])
    min_y = min([point[1] for road in coords for point in road])
    max_y = max([point[1] for road in coords for point in road])
    
    def scale(point):
        x = margin + (point[0] - min_x) / (max_x - min_x) * (width - 2 * margin)
        y = height - (margin + (point[1] - min_y) / (max_y - min_y) * (height - 2 * margin))
        return (int(x), int(y))
    
    return [[scale(point) for point in road] for road in coords]

# 변환된 좌표
width, height = 800, 600
transformed_roads = transform_coordinates(road_coords, width, height)

# 디버깅: 변환된 좌표 확인
if transformed_roads:
    print("변환된 첫 번째 도로의 좌표:", transformed_roads[0])
else:
    print("변환된 도로 데이터가 없습니다.")

import pygame
import sys

# pygame 초기화
pygame.init()

# 화면 설정
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Road Network Visualization')

# 색상 설정
white = (255, 255, 255)
black = (0, 0, 0)
blue = (0, 0, 255)

# 메인 루프
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()
    
    # 화면을 흰색으로 채우기
    screen.fill(white)
    
    # 도로 데이터 그리기
    for road in transformed_roads:
        if road:
            pygame.draw.lines(screen, blue, False, road, 2)
    
    # 화면 업데이트
    pygame.display.flip()
