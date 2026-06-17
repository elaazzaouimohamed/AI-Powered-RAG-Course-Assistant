import { useState } from 'react';
import './QuizCard.css';

/**
 * Affiche une question de quiz avec ses choix de réponse.
 *
 * Gère la sélection d'une réponse et l'affichage du feedback
 * (correct / incorrect + explication) après validation.
 *
 * @param {object}   props
 * @param {object}   props.question         - objet Question { questionText, choices, correctAnswerIndex, explanation }
 * @param {number}   props.questionNumber   - numéro affiché (1-based)
 * @param {Function} props.onAnswer         - appelé avec l'indice de la réponse choisie
 * @param {boolean}  props.answered         - true si la réponse a déjà été soumise
 * @param {number}   [props.selectedIndex]  - indice de la réponse déjà sélectionnée
 */
export default function QuizCard({ question, questionNumber, onAnswer, answered = false, selectedIndex }) {
  const [hovered, setHovered] = useState(null);

  function handleSelect(index) {
    if (answered) return;
    onAnswer(index);
  }

  return (
    <div className="quiz-card">
      <p className="quiz-card__number">Question {questionNumber}</p>
      <p className="quiz-card__question">{question.questionText}</p>

      <ul className="quiz-card__choices">
        {question.choices.map((choice, index) => {
          let choiceClass = 'quiz-card__choice';
          if (answered) {
            if (index === question.correctAnswerIndex) choiceClass += ' quiz-card__choice--correct';
            else if (index === selectedIndex)          choiceClass += ' quiz-card__choice--wrong';
          } else if (hovered === index) {
            choiceClass += ' quiz-card__choice--hovered';
          }

          return (
            <li key={index}>
              <button
                className={choiceClass}
                onClick={() => handleSelect(index)}
                onMouseEnter={() => setHovered(index)}
                onMouseLeave={() => setHovered(null)}
                disabled={answered}
              >
                {choice}
              </button>
            </li>
          );
        })}
      </ul>

      {/* Explication affichée après la réponse */}
      {answered && question.explanation && (
        <p className="quiz-card__explanation">{question.explanation}</p>
      )}
    </div>
  );
}
