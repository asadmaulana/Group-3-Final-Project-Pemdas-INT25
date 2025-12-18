import pygame
import random
import operator
from typing import List, Tuple, Optional

OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '×': operator.mul,
    '÷': operator.floordiv
}

class MathExpressionGenerator:
    
    def __init__(self, min_result: int = 2, max_result: int = 50):
        self.min_result = min_result
        self.max_result = max_result
    
    def generate_addition(self, target: int) -> str:
        a = random.randint(1, target - 1)
        b = target - a
        if random.random() < 0.5:
            return f"{a} + {b}"
        return f"{b} + {a}"
    
    def generate_subtraction(self, target: int) -> str:
        b = random.randint(1, min(30, target))
        a = target + b
        if a <= 100:
            return f"{a} - {b}"
        return self.generate_addition(target)
    
    def generate_multiplication(self, target: int) -> str:
        factors = []
        for i in range(1, int(target**0.5) + 1):
            if target % i == 0:
                factors.append((i, target // i))
        
        if factors:
            a, b = random.choice(factors)
            if random.random() < 0.5:
                return f"{a} × {b}"
            return f"{b} × {a}"
        return self.generate_addition(target)
    
    def generate_division(self, target: int) -> str:
        b = random.randint(2, min(12, target))
        a = target * b
        if a <= 144:
            return f"{a} ÷ {b}"
        return self.generate_multiplication(target)
    
    def generate_expression(self, target: int, attempts: int = 10) -> str:
        for _ in range(attempts):
            op_type = random.choice(['add', 'sub', 'mul', 'div'])
            
            if op_type == 'add':
                expr = self.generate_addition(target)
            elif op_type == 'sub':
                expr = self.generate_subtraction(target)
            elif op_type == 'mul':
                expr = self.generate_multiplication(target)
            else:
                expr = self.generate_division(target)

            if self.evaluate(expr) == target:
                return expr

        return self.generate_addition(target)
    
    def evaluate(self, expression: str) -> int:
        try:
            expr = expression.replace('×', '*').replace('÷', '//')
            return eval(expr)
        except:
            return -1
    
    def generate_unique_expressions(self, target: int, count: int = 2) -> List[str]:
        expressions = set()
        max_attempts = count * 10
        attempts = 0
        
        while len(expressions) < count and attempts < max_attempts:
            expr = self.generate_expression(target)
            if expr not in expressions:
                expressions.add(expr)
            attempts += 1

        while len(expressions) < count:
            expressions.add(self.generate_addition(target))
        
        return list(expressions)


class NightmareCardGenerator:
    
    def __init__(self):
        self.generator = MathExpressionGenerator()
    
    def generate_cards(self, num_pairs: int) -> List[Tuple[str, int]]:
        targets = set()
        while len(targets) < num_pairs:
            target = random.randint(self.generator.min_result, 
                                   self.generator.max_result)
            if target != 1 and target <= self.generator.max_result:
                targets.add(target)
        
        targets = list(targets)
        cards = []
        
        for target in targets:
            expressions = self.generator.generate_unique_expressions(target, 2)

            while len(expressions) < 2:
                new_expr = self.generator.generate_expression(target)
                if new_expr not in expressions:
                    expressions.append(new_expr)

            cards.append((expressions[0], target))
            cards.append((expressions[1], target))

        random.shuffle(cards)
        return cards


class NightmareCard:
    def __init__(self, rect: pygame.Rect, expression: str, answer: int):
        self.rect = rect
        self.expression = expression
        self.answer = answer
        self.id = answer
        self.flipped = False
        self.matched = False
        self.flip_progress = 0
        self.target_flip = 0
    
    def start_flip(self, show_front: bool) -> None:
        self.target_flip = 1 if show_front else 0
    
    def update_animation(self, flip_speed: float = 0.15) -> None:
        if self.flip_progress < self.target_flip:
            self.flip_progress = min(1, self.flip_progress + flip_speed)
        elif self.flip_progress > self.target_flip:
            self.flip_progress = max(0, self.flip_progress - flip_speed)
        
        if abs(self.flip_progress - self.target_flip) < 0.01:
            self.flipped = (self.target_flip == 1)
    
    def draw(self, screen: pygame.Surface, font: pygame.font.Font, back_symbol: str = "?"):
        show_front = self.matched or self.flip_progress > 0.5

        scale_x = abs(1 - 2 * self.flip_progress)
        if scale_x < 0.1:
            scale_x = 0.1

        scaled_w = int(self.rect.w * scale_x)
        scaled_h = self.rect.h
        
        if scaled_w <= 0:
            return

        offset_x = (self.rect.w - scaled_w) // 2
        scaled_rect = pygame.Rect(
            self.rect.x + offset_x,
            self.rect.y,
            scaled_w,
            scaled_h
        )

        if self.matched:
            bg_color = (50, 120, 50)
        elif show_front:
            bg_color = (70, 70, 100)
        else:
            bg_color = (60, 60, 80)

        pygame.draw.rect(screen, bg_color, scaled_rect, border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), scaled_rect, 2, border_radius=12)

        if scale_x < 0.3:
            return
        
        text_to_show = self.expression if show_front else back_symbol
        text_color = (200, 255, 200) if self.matched else (240, 240, 240)

        text_surf = font.render(text_to_show, True, text_color)

        text_w = int(text_surf.get_width() * scale_x)
        if text_w > 0:
            try:
                scaled_text = pygame.transform.smoothscale(
                    text_surf, 
                    (text_w, text_surf.get_height())
                )
                text_rect = scaled_text.get_rect(center=scaled_rect.center)
                screen.blit(scaled_text, text_rect)
            except:
                pass


class NightmareBoard:
    
    def __init__(self, rows: int = 4, cols: int = 4):
        self.rows = rows
        self.cols = cols
        self.cards = []

        num_pairs = (rows * cols) // 2
        card_generator = NightmareCardGenerator()
        card_data = card_generator.generate_cards(num_pairs)

        screen_width, screen_height = 800, 600
        card_w, card_h = 100, 100
        padding = 12
        
        total_w = cols * card_w + (cols - 1) * padding
        total_h = rows * card_h + (rows - 1) * padding
        start_x = (screen_width - total_w) // 2
        start_y = (screen_height - total_h) // 2
        
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        
        for i, (expression, answer) in enumerate(card_data):
            row = i // cols
            col = i % cols
            x = start_x + col * (card_w + padding)
            y = start_y + row * (card_h + padding)
            
            card = NightmareCard(
                pygame.Rect(x, y, card_w, card_h),
                expression,
                answer
            )
            self.cards.append(card)
    
    def update(self) -> None:
        for card in self.cards:
            card.update_animation()
    
    def draw(self, screen: pygame.Surface) -> None:
        for card in self.cards:
            card.draw(screen, self.font)
    
    def all_matched(self) -> bool:
        return all(card.matched for card in self.cards)

if __name__ == "__main__":
    pygame.init()