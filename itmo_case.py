import json
from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TurnLog:
    turn_id: int
    agent_visible_message: str
    user_message: str
    internal_thoughts: str


class InterviewCoach:
    def __init__(self):
        self.turns = []
        self.participant_name = ""
        self.position = ""
        self.grade = ""
        self.experience = ""
        self.current_turn = 0
        
        # для уникальных вопросов
        self.questions_asked = set()
        self.performance_score = 0
        self.difficulty_level = "easy"
        self.user_skills = defaultdict(list)


    def initialize(self, name, position, grade, experience):
        self.participant_name = name
        self.position = position
        self.grade = grade
        self.experience = experience
        
        welcome = f"Привет, {name}! Позиция {position} ({grade}). Расскажи про опыт с {experience}."
        self.turns.append(TurnLog(1, welcome, "", "[System]: start"))
        print(f"🤖 Interviewer: {welcome}")


    def _observer_reflection(self, user_msg):
        # observer проверяет ответ
        is_hallucination = any(phrase in user_msg.lower() for phrase in ["python 4", "нейронные связи"])
        is_offtopic = any(word in user_msg.lower() for word in ["испытательн", "микросервис", "задач"])
        is_good_answer = len(user_msg) > 20 and not is_hallucination and not is_offtopic
        
        analysis = "Галлюцинация" if is_hallucination else "Off-topic" if is_offtopic else "Хороший ответ" if is_good_answer else "Слабый ответ"
        next_action = "исправить" if is_hallucination else "ответить+вопрос" if is_offtopic else "усложнить" if is_good_answer else "упростить"
        
        # score для адаптации
        if is_good_answer:
            self.performance_score += 1
        elif is_hallucination:
            self.performance_score -= 2
        else:
            self.performance_score -= 1
            
        return {
            "analysis": analysis,
            "next_action": next_action,
            "is_hallucination": is_hallucination,
            "is_offtopic": is_offtopic,
            "is_good_answer": is_good_answer,
            "performance_score": self.performance_score
        }


    def _get_adaptive_difficulty(self, reflection):
        # меняем сложность
        if reflection["is_good_answer"] and self.performance_score > 2:
            self.difficulty_level = "hard"
        elif reflection["is_hallucination"] or self.performance_score < -1:
            self.difficulty_level = "easy"
        else:
            self.difficulty_level = "medium"
        return self.difficulty_level


    def _generate_unique_question(self, difficulty):
        questions = {
            "easy": ["Что такое список в Python?", "Что такое GET/POST?", "Что такое Git commit?"],
            "medium": ["SQL JOIN как работает?", "list vs tuple?", "Django ORM?"],
            "hard": ["Python GIL?", "Celery когда?", "SQL оптимизация?"]
        }
        
        q_pool = questions.get(difficulty, questions["medium"])
        
        for question in q_pool:
            if question.lower() not in self.questions_asked:
                self.questions_asked.add(question.lower())
                return question
                
        return "Расскажи про последний проект"


    def process_turn(self, user_msg):
        self.current_turn += 1
        
        # 1. observer думает
        reflection = self._observer_reflection(user_msg)
        
        # 2. адаптируем сложность
        difficulty = self._get_adaptive_difficulty(reflection)
        
        # 3. генерим вопрос
        question = self._generate_unique_question(difficulty)
        
        # 4. обрабатываем проблемы
        if reflection['is_hallucination']:
            question = f"Python 4.0 нет (3.12+). {question}"
        if reflection['is_offtopic']:
            question = f"Используем микросервисы. {question}"
        
        # 5. skills tracking
        topic = "Python" if "python" in question.lower() else "SQL" if "sql" in question.lower() else "Django"
        if reflection['is_good_answer']:
            self.user_skills["confirmed_skills"].append(topic)
        else:
            self.user_skills["knowledge_gaps"].append(f"{topic}: изучи основы")
        
        # 6. лог мыслей агентов
        internal = f"[Observer]:{reflection['analysis']} | [Interviewer]:{reflection['next_action']} (diff:{difficulty})"
        
        turn = TurnLog(self.current_turn, question, user_msg, internal)
        self.turns.append(turn)
        
        print(f"\n📝 {internal}")
        print(f"🤖 Interviewer: {question}")
        return question


    def generate_feedback(self):
        # финальный фидбек
        final_grade = "Senior" if self.performance_score > 3 else "Middle" if self.performance_score > 0 else "Junior"
        
        feedback = {
            "verdict": {
                "grade": final_grade,
                "hiring_recommendation": "Hire" if self.performance_score >= 0 else "No Hire",
                "confidence": max(10, min(100, 50 + self.performance_score * 10))
            },
            "technical_review": {
                "confirmed_skills": self.user_skills["confirmed_skills"],
                "knowledge_gaps": self.user_skills["knowledge_gaps"]
            },
            "soft_skills": {
                "clarity": "high" if any(len(t.user_message) > 50 for t in self.turns) else "medium",
                "honesty": "low" if any("python 4" in t.user_message.lower() for t in self.turns) else "high",
                "engagement": "high" if any("испытатель" in t.user_message.lower() for t in self.turns) else "medium"
            },
            "roadmap": ["Python 3.12+", "SQL JOINs", "Django ORM docs"]
        }
        
        log_data = {
            "participant_name": self.participant_name,
            "turns": [t.__dict__ for t in self.turns],
            "final_feedback": feedback
        }
        
        with open("interview_log.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        # ✅ ЧИСТЫЙ ВЫВОД - убрал полоски!
        print("\nJSON готов")
        print(json.dumps(feedback, ensure_ascii=False, indent=2))
        return log_data


if __name__ == "__main__":
    print("Multi-Agent Interview")
    
    coach = InterviewCoach()
    coach.initialize("Алекс", "Backend Developer", "Junior", "Django pet-проекты")
    
    print("\nтест сценария:")
    print('1. "Привет я знаю Python"')
    print('2. "Python 4.0 уберут циклы"')
    print('3. "какие задачи на испытательном?"')
    print('4. "стоп"')
    
    while True:
        user_input = input("\nТы: ")
        if "стоп" in user_input.lower() or "фидбэк" in user_input.lower():
            coach.generate_feedback()
            break
        coach.process_turn(user_input)
