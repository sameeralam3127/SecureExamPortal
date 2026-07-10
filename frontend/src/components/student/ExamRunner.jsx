function formatTimer(value) {
  const minutes = Math.floor(value / 60)
  const seconds = value % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function AssignedExamList({ studentAssignments, onStart }) {
  return (
    <section className="white-panel">
      <h2>Assigned Exams</h2>
      <div className="list-stack">
        {studentAssignments.length ? (
          studentAssignments.map((assignment) => (
            <div className="row-card row-flex" key={assignment.assignment_id}>
              <div>
                <strong>{assignment.exam_title}</strong>
                <p>
                  Duration {assignment.duration_minutes} mins | Status{' '}
                  {assignment.status || 'not started'}
                </p>
              </div>
              <button
                className="action-btn blue compact-btn"
                type="button"
                disabled={assignment.status === 'submitted'}
                onClick={() => onStart(assignment.assignment_id)}
              >
                {assignment.status === 'in_progress' ? 'Resume' : 'Start'}
              </button>
            </div>
          ))
        ) : (
          <p className="helper-text">No exams assigned yet.</p>
        )}
      </div>
    </section>
  )
}

export default function ExamRunner({
  liveExam,
  studentAssignments,
  answers,
  currentQuestionIndex,
  setCurrentQuestionIndex,
  isReviewMode,
  setIsReviewMode,
  autosaveState,
  secondsLeft,
  securityWarning,
  autosaveAnswer,
  submitExam,
  onStart,
}) {
  if (!liveExam) {
    return <AssignedExamList studentAssignments={studentAssignments} onStart={onStart} />
  }

  const currentQuestion = liveExam.questions?.[currentQuestionIndex] || null
  const answeredCount = liveExam.questions.filter((question) => Boolean(answers[question.id])).length
  const firstUnanswered = liveExam.questions.findIndex((question) => !answers[question.id])
  const furthestAccessibleIndex = Math.min(
    firstUnanswered === -1 ? liveExam.question_count - 1 : firstUnanswered,
    liveExam.question_count - 1,
  )

  return (
    <section className="white-panel">
      <div className="exam-header">
        <div>
          <h2>{liveExam.title}</h2>
          <p className="helper-text">
            {liveExam.description} | Answered {answeredCount}/{liveExam.question_count}
          </p>
        </div>
        <div className="exam-status-block">
          <div className={`timer-pill ${secondsLeft < 60 ? 'urgent' : ''}`}>
            {formatTimer(secondsLeft)}
          </div>
          <span className="autosave-text">{autosaveState || 'Autosave ready'}</span>
        </div>
      </div>
      <div className="security-policy-strip">
        <span>{liveExam.block_clipboard ? 'Clipboard blocked' : 'Clipboard allowed'}</span>
        <span>{liveExam.block_context_menu ? 'Right-click blocked' : 'Right-click allowed'}</span>
        <span>{liveExam.track_focus_loss ? 'Focus monitored' : 'Focus not monitored'}</span>
        <span>{liveExam.enforce_fullscreen ? 'Fullscreen required' : 'Fullscreen optional'}</span>
      </div>
      {securityWarning ? <div className="security-warning">{securityWarning}</div> : null}
      <div className="question-progress-row">
        {liveExam.questions.map((question, index) => (
          <button
            key={question.id}
            type="button"
            className={`question-pill ${
              index === currentQuestionIndex && !isReviewMode ? 'active-pill' : ''
            } ${answers[question.id] ? 'answered-pill' : ''}`}
            disabled={index > furthestAccessibleIndex}
            onClick={() => {
              if (index <= furthestAccessibleIndex) {
                setCurrentQuestionIndex(index)
              }
            }}
          >
            {index + 1}
          </button>
        ))}
      </div>
      {isReviewMode ? (
        <div className="list-stack">
          {liveExam.questions.map((question, index) => (
            <div className="question-card" key={question.id}>
              <strong>
                {index + 1}. {question.question_text}
              </strong>
              <p className="helper-text">
                Selected answer: {answers[question.id] ? `${answers[question.id]}` : 'Not answered'}
              </p>
              <button
                className="mini-btn"
                type="button"
                onClick={() => {
                  setCurrentQuestionIndex(index)
                  setIsReviewMode(false)
                }}
              >
                Edit answer
              </button>
            </div>
          ))}
          <div className="inline-fields">
            <button className="action-btn green" type="button" onClick={() => setIsReviewMode(false)}>
              Back to Questions
            </button>
            <button className="action-btn blue" type="button" onClick={submitExam}>
              Submit Exam
            </button>
          </div>
        </div>
      ) : (
        currentQuestion && (
          <div className="question-card">
            <strong>
              Question {currentQuestionIndex + 1} of {liveExam.question_count}
            </strong>
            <h3 className="question-title">{currentQuestion.question_text}</h3>
            {['A', 'B', 'C', 'D'].map((optionKey) => (
              <label className="option-choice" key={`${currentQuestion.id}-${optionKey}`}>
                <input
                  type="radio"
                  name={`question-${currentQuestion.id}`}
                  checked={answers[currentQuestion.id] === optionKey}
                  onChange={() => autosaveAnswer(currentQuestion.id, optionKey)}
                />
                <span>
                  {optionKey}. {currentQuestion[`option_${optionKey.toLowerCase()}`]}
                </span>
              </label>
            ))}
            <div className="inline-fields">
              <button
                className="action-btn green"
                type="button"
                disabled={currentQuestionIndex === 0}
                onClick={() => setCurrentQuestionIndex((index) => Math.max(index - 1, 0))}
              >
                Previous
              </button>
              {currentQuestionIndex < liveExam.question_count - 1 ? (
                <button
                  className="action-btn blue"
                  type="button"
                  onClick={() =>
                    setCurrentQuestionIndex((index) =>
                      Math.min(index + 1, liveExam.question_count - 1),
                    )
                  }
                >
                  Next
                </button>
              ) : (
                <button
                  className="action-btn yellow"
                  type="button"
                  onClick={() => setIsReviewMode(true)}
                >
                  Review Answers
                </button>
              )}
            </div>
          </div>
        )
      )}
    </section>
  )
}
