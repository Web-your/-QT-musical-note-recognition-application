import cv2
import numpy as np
import copy
from numpy.ma.core import append

def merged_noty_contours(contours, merged_axis="x", *distance_contours):
    if not contours:
        return []
    rects = [cv2.boundingRect(cnt) for cnt in contours]
    if merged_axis[0] == "x":
        rects.sort(key=lambda x: x[0])
        print(rects)
        i = 0
        while i < len(rects):
            x1, y1, w1, h1 = rects[i]
            j = i + 1
            while j < len(rects):
                x2, y2, w2, h2 = rects[j]
                if abs(x1 + w1 - x2) <= distance_contours[0]:
                    if merged_axis[-1] == "s":
                        if abs((w1 * h1) - (w2 * h2)) <= distance_contours[1]:
                            rects[i] = x1, y1, w1 + w2, (h1 + h2) / 2
                            del rects[j]
                    else:
                        rects[i] = x1, y1, w1 + w2, (h1 + h2) / 2
                        del rects[j]
                j += 1
            i += 1
    elif merged_axis[0] == "y":
        rects.sort(key=lambda x: -x[1])
        i = 0
        while i < len(rects):
            x1, y1, w1, h1 = rects[i]
            j = i + 1
            while j < len(rects):
                x2, y2, w2, h2 = rects[j]
                if abs(y1 - y2) <= distance_contours[0]:
                    if merged_axis[-1] == "s":
                        if abs((w1 * h1) - (w2 * h2)) <= distance_contours[1]:
                            rects[i] = x1, y1, w1 + w2, (h1 + h2) / 2
                            del rects[j]
                    else:
                        rects[i] = x1, y1, w1 + w2, (h1 + h2) / 2
                        del rects[j]
                j += 1
            i += 1
    elif merged_axis[:1] == "xy":
        rects.sort(key=lambda x: x[0])
        i = 0
        while i < len(rects):
            x1, y1, w1, h1 = rects[i]
            j = i + 1
            while j < len(rects):
                x2, y2, w2, h2 = rects[j]
                if abs(x1 + w1 - x2) <= distance_contours[0] and abs(y1 - y2) <= distance_contours[1]:
                    if merged_axis[-1] == "s":
                        if abs((w1 * h1) - (w2 * h2)) <= distance_contours[2]:
                            rects[i] = x1, y1, w1 + w2, (h1 + h2) / 2
                            del rects[j]
                    else:
                        rects[i] = x1, y1, w1 + w2, (h1 + h2) / 2
                        del rects[j]
                j += 1
            i += 1
    result = []
    for x, y, w, h in rects:
        contour = np.array([
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ], dtype=np.int32)
        result.append(contour)

    return result


def merged_noty_line(lines, line_distance, up_down="up"):
    otv = list(lines)
    otv.sort(key=lambda x:-x[0][1])
    i = 0
    while i < len(otv):
        x1, y1, x2, y2 = otv[i][0]
        j = i + 1
        while j < len(otv):
            x3, y3, x4, y4 = otv[j][0]
            if (abs(y3 - y1) + abs(y4 - y2)) / 2 <= line_distance:
                if up_down == "up":
                    del otv[j]
                elif up_down == "down":
                    del otv[i]
            j += 1
        i += 1
    return otv

def completion_noty_line(lines, line_distance):
    otv = list(lines)
    otv.sort(key=lambda x: -x[0][1])
    for i in range(len(otv) - 1):
        x1, y1, x2, y2 = otv[i][0]
        x3, y3, x4, y4 = otv[i + 1][0]
        if (abs(y3 - y1) + abs(y4 - y2)) / 2 >= line_distance:
            otv.append(np.array([[x3, y3 + (line_distance / 1.1), x4,   y4 + (line_distance / 1.1)]], dtype="int32"))
    return otv



def merged_contours(contours):
    if not contours:
        return []

    # Сначала преобразуем все контуры в прямоугольники (x, y, w, h)
    rects = [cv2.boundingRect(cnt) for cnt in contours]
    changed = True

    # Будем повторять объединение, пока есть изменения
    while changed:
        changed = False
        new_rects = []
        used = [False] * len(rects)

        for i in range(len(rects)):
            if used[i]:
                continue

            x1, y1, w1, h1 = rects[i]
            merged = False

            # Проверяем со всеми последующими прямоугольниками
            for j in range(i + 1, len(rects)):
                if used[j]:
                    continue

                x2, y2, w2, h2 = rects[j]

                # Проверяем пересечение
                if (x1 < x2 + w2) and (x1 + w1 > x2) and \
                        (y1 < y2 + h2) and (y1 + h1 > y2):
                    # Объединяем прямоугольники
                    new_x = min(x1, x2)
                    new_y = min(y1, y2)
                    new_w = max(x1 + w1, x2 + w2) - new_x
                    new_h = max(y1 + h1, y2 + h2) - new_y

                    new_rects.append((new_x, new_y, new_w, new_h))
                    used[i] = used[j] = True
                    merged = True
                    changed = True
                    break

            if not merged:
                new_rects.append(rects[i])
                used[i] = True

        rects = new_rects

    # Преобразуем прямоугольники обратно в контуры
    result = []
    for x, y, w, h in rects:
        contour = np.array([
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ], dtype=np.int32)
        result.append(contour)

    return result


def merge_lines(lines, vertical_or_horizontal=0, distance_lines=10):
    """
    Объединяет близкие или пересекающиеся вертикальные линии
    :param lines: Входные линии в формате numpy array shape=(N,1,4)
    :return: Объединенные линии в том же формате
    """
    if vertical_or_horizontal > 0:
        cnt1 = -10
        cnt2 = 10
        flag = False
    else:
        cnt1 = 85
        cnt2 = 95
        flag = True
    if lines is None or lines.size == 0:
        return np.empty((0, 1, 4), dtype=np.int32)

    # Фильтруем только вертикальные линии (±10° от вертикали)
    vertical_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(angle) > cnt1 and abs(angle) < cnt2:  # Допуск ±10°
            vertical_lines.append([x1, y1, x2, y2])

    if not vertical_lines:
        return np.empty((0, 1, 4), dtype=np.int32)

    vertical_lines = np.array(vertical_lines)

    # Процесс объединения
    merged = True
    while merged:
        merged = False
        new_lines = []
        used = [False] * len(vertical_lines)

        for i in range(len(vertical_lines)):
            if used[i]:
                continue

            x1_i, y1_i, x2_i, y2_i = vertical_lines[i]
            current_line = vertical_lines[i]

            for j in range(i + 1, len(vertical_lines)):
                if used[j]:
                    continue

                x1_j, y1_j, x2_j, y2_j = vertical_lines[j]

                # Проверяем близость по X (расстояние между линиями < 10 пикселей)
                if abs(x1_i - x1_j) < distance_lines and flag:
                    # Объединяем линии
                    new_x = (x1_i + x1_j) // 2  # Среднее положение
                    new_y1 = min(y1_i, y1_j)  # Верхняя точка
                    new_y2 = max(y2_i, y2_j)  # Нижняя точка

                    current_line = np.array([new_x, new_y1, new_x, new_y2])
                    used[j] = True
                    merged = True

                if abs(y1_i - y1_j) < distance_lines and not flag:
                    # Объединяем линии
                    new_x = (x1_i + x1_j) // 2  # Среднее положение
                    new_y1 = min(y1_i, y1_j)  # Верхняя точка
                    new_y2 = max(y2_i, y2_j)  # Нижняя точка

                    current_line = np.array([new_x, new_y1, new_x, new_y2])
                    used[j] = True
                    merged = True

            new_lines.append(current_line)
            used[i] = True

        vertical_lines = np.array(new_lines)

    # Возвращаем в исходном формате (N,1,4)
    return vertical_lines.reshape(-1, 1, 4).astype(np.int32)


def distribute_cut(merged_true, clear_img):
    imges = []
    images_edges = []
    images_edges_ = []
    for cnt in range(len(merged_true)):
        x, y, w, h = cv2.boundingRect(merged_true[cnt])
        image = clear_img[y:y + h, x:x + w]
        imges.append(image)
        image_edges = cv2.Canny(image, 50, 150)
        images_edges.append(image_edges)
        _, thresh = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY_INV)
        images_edges_.append(thresh)
        # cv2.imshow(f'Detected Objects{cnt}', image_edges)
    return imges, images_edges, images_edges_

def scan_note(file_path, algorithm, size=5, binar=100, blur_s=3, axis="xys"):
    if file_path == "":
        return []
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    blur = cv2.GaussianBlur(img, (blur_s + 2, blur_s + 2), 0)
    edges = cv2.Canny(blur, 50, 150)  # 50 и 150 — пороги чувствительности
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    true_contour = np.array([[0, 0], [0, 0], [0, 0], [0, 0]])
    for cnt in contours:
        if cv2.contourArea(cnt) > 100 and cv2.contourArea(cnt) > cv2.contourArea(true_contour):
            true_contour = cnt

    x, y, w, h = cv2.boundingRect(true_contour) # Получаем координаты прямоугольника
    if algorithm == "clipping":
        clear_img = img[y:y + h, x:x + w]
    else:
        clear_img = img
    blur = cv2.GaussianBlur(clear_img, (blur_s, blur_s), 0)
    edges = cv2.Canny(blur, 50, 150)
    # cv2.imshow('Edges', edges)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_true = []
    for cnt in contours:
        if cv2.contourArea(cnt) > 100:  # and cv2.contourArea(cnt) >= (len(img[1]) * 0.8)
            contours_true.append(cnt)

    # img_vis = img
    merged_true = merged_contours(contours_true)
    for i in contours_true:
        x, y, w, h = cv2.boundingRect(i)
        # cv2.rectangle(img_vis, (x, y), (x + w, y + h), (0, 0, 255), 2)
    # cv2.imwrite(f'result.jpg', img_vis)

    notes = []
    imges, images_edges, _ = distribute_cut(merged_true, clear_img)
    for cny in range(len(images_edges)):
        lst_notelines = []
        lst_note = []

        a = (len(imges[cny][1]) * 0.8)
        b = (len(imges[cny]) * 0.1)
        lines = cv2.HoughLinesP(images_edges[cny], 1, np.pi / 180, threshold=20, minLineLength=a, maxLineGap=50)
        merged_lines = merge_lines(lines, 1, 1)
        merged_lines = merged_noty_line(merged_lines, b, "up")
        for i in range(len(merged_lines) - 1):
            x1, y1, x2, y2 = merged_lines[i][0]
            x3, y3, x4, y4 = merged_lines[i + 1][0]
            if (abs(y3 - y1) + abs(y4 - y2)) / 2 <= b and len(merged_lines) != 5:
                merged_lines = merged_noty_line(merged_lines, b, "down")
                break
        attempts = 0
        while len(merged_lines) != 5 and attempts <= size:
            if len(merged_lines) > 5:
                n = []  # числа разности
                for i in range(len(merged_lines) - 1):
                    x1, y1, x2, y2 = merged_lines[i][0]
                    x3, y3, x4, y4 = merged_lines[i + 1][0]
                    n.append((abs(y3 - y1) + abs(y4 - y2)) / 2)
                b = max(n) * 1.3
                merged_lines = merged_noty_line(merged_lines, b)
            elif 0 < len(merged_lines) < 5:
                n = []  # числа разности
                for i in range(len(merged_lines) - 1):
                    x1, y1, x2, y2 = merged_lines[i][0]
                    x3, y3, x4, y4 = merged_lines[i + 1][0]
                    n.append((abs(y3 - y1) + abs(y4 - y2)) / 2)
                b = min(n) * 1.1
                merged_lines = completion_noty_line(merged_lines, b)
            attempts += 1


        for line in merged_lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(imges[cny], (x1, y1), (x2, y2), (255, 255, 255), 2)
            lst_notelines.append(y1)
        lst_notelines.sort()
        # cv2.imshow(f'Detected image{cny}', imges[cny])

        _, thresh = cv2.threshold(imges[cny], binar, 255, cv2.THRESH_BINARY_INV)
        images_edges_ = thresh  # cv2.erode(thresh, np.ones((1, 2), np.uint8), iterations=1)
        # cv2.imwrite(f'note_img{cny}.jpg', imges[cny])

        contours, _ = cv2.findContours(images_edges_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        true_contour = []

        for cnt in contours:
            if cv2.contourArea(cnt) > 1:  # Игнорируем мелкие объекты
                x, y, w, h = cv2.boundingRect(cnt)
                perimeter = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)
                if len(approx) > 6:
                    (x, y), radius = cv2.minEnclosingCircle(cnt)
                    area = cv2.contourArea(cnt)
                    circularity = 4 * np.pi * area / (perimeter ** 2)

                    # Круглость близка к 1? (1 — идеальная окружность)
                    if 0.1 < circularity < 1.5:
                        print("нота")
                        true_contour.append(cnt)
                        # x, y, w, h = cv2.boundingRect(cnt)
                        # x, y, w, h = map(int, (x, y, w, h))
                        # cl = imges[cny][0:, x  - (2 * w):x + (3 * w)]
                        # ing = images_edges_[0:, x  - (2 * w):x + (3 * w)]
                        # lines = cv2.HoughLinesP(ing, 1, np.pi / 2, threshold=20, minLineLength=3, maxLineGap=50)
                        # merged_lines = merge_lines(lines)
                        # for line in merged_lines:
                        #    x1, y1, x2, y2 = line[0]
                        #    cv2.line(cl, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        # cv2.imshow(f'Detected note{cnt}', cl)
        contours_note = merged_noty_contours(true_contour, axis, 20, 20, 10)
        lst_note = contours_note
        for i in contours_note:
            x, y, w, h = cv2.boundingRect(i)
            cv2.rectangle(imges[cny], (x, y), (x + w, y + h), (0, 255, 0), 2)
            x, y, w, h = map(int, (x, y, w, h))
            cl = imges[cny][0:, x - (2 * w):x + (3 * w)]
            ing = images_edges_[0:, x - (2 * w):x + (3 * w)]
            lines = cv2.HoughLinesP(ing, 1, np.pi / 2, threshold=20, minLineLength=3, maxLineGap=50)
            merged_lines = merge_lines(lines)
            for line in merged_lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(cl, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # cv2.imwrite(f'note_detected{cny}.jpg', imges[cny])

        # распределение нот по высотам

        if len(lst_notelines) == 0:
            continue
        n = []
        for i in range(len(lst_notelines) - 1):
            n.append(abs(lst_notelines[i] - lst_notelines[i + 1]))
        difference_not = (min(n) * 0.9) / 2
        note_res = []
        for note in lst_note:
            x, y, w, h = cv2.boundingRect(note)
            point_note = y + (h / 2)
            note_type = "None"
            if lst_notelines[0] - difference_not > point_note:
                note_type = "c"
            elif lst_notelines[0] - difference_not < point_note < lst_notelines[0]:
                note_type = "d"
            elif lst_notelines[0] - difference_not < point_note < lst_notelines[0] + difference_not:
                note_type = "e"
            elif lst_notelines[0] < point_note < lst_notelines[1]:
                note_type = "f"
            elif lst_notelines[1] - difference_not < point_note < lst_notelines[1] + difference_not:
                note_type = "g"
            elif lst_notelines[1] < point_note < lst_notelines[2]:
                note_type = "a"
            elif lst_notelines[2] - difference_not < point_note < lst_notelines[2] + difference_not:
                note_type = "h"
            old_x, old_y, old_w, old_h = cv2.boundingRect(merged_true[cny])
            contour_note = [old_x + x, old_y + y, w, h]
            if note_type != "None":
                note_res.append([note_type, contour_note])
        note_res.sort(key=lambda x: x[1][0])
        notes.append(note_res)
    notes.sort(key=lambda x: x[0][1][1])
    return notes
