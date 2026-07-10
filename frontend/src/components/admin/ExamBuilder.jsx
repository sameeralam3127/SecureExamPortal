import { validateExamForm } from '../../hooks/useAdminPortal.js'

export default function ExamBuilder({
  examForm,
  setExamForm,
  updateExamQuestion,
  addQuestion,
  removeQuestion,
  onCreateExam,
  exams,
  onDeleteExam,
  bulkExamsText,
  setBulkExamsText,
  onBulkUpload,
}) {
  const totalMarks = examForm.questions.reduce(
    (sum, question) => sum + (Number(question.marks) || 0),
    0,
  )
  const validationError = validateExamForm(examForm)

  const securityToggles = [
    ['block_clipboard', 'Block copy, paste, and cut'],
    ['block_context_menu', 'Block right-click menu'],
    ['block_inspect_shortcuts', 'Block inspect/developer shortcuts'],
    ['track_focus_loss', 'Log tab switches and window focus loss'],
    ['enforce_fullscreen', 'Require fullscreen during exam'],
  ]

  return (
    <section className="admin-stack">
      <section className="two-grid">
        <article className="white-panel">
          <div className="panel-title-row">
            <h2>Create Exam</h2>
            <span className="pill-badge">
              {examForm.questions.length} question{examForm.questions.length === 1 ? '' : 's'} ·{' '}
              {totalMarks} marks
            </span>
          </div>
          <form className="form-stack" onSubmit={onCreateExam}>
            <div className="inline-fields">
              <input
                placeholder="Exam title"
                aria-label="Exam title"
                value={examForm.title}
                onChange={(event) =>
                  setExamForm((current) => ({ ...current, title: event.target.value }))
                }
                required
                minLength={3}
              />
              <input
                type="number"
                min="1"
                max="600"
                aria-label="Duration in minutes"
                value={examForm.duration_minutes}
                onChange={(event) =>
                  setExamForm((current) => ({ ...current, duration_minutes: event.target.value }))
                }
                required
              />
            </div>
            <textarea
              placeholder="Description"
              aria-label="Exam description"
              value={examForm.description}
              onChange={(event) =>
                setExamForm((current) => ({ ...current, description: event.target.value }))
              }
              required
            />
            <div className="security-policy-box">
              <strong>Security Policies</strong>
              {securityToggles.map(([field, label]) => (
                <label key={field}>
                  <input
                    type="checkbox"
                    checked={examForm[field]}
                    onChange={(event) =>
                      setExamForm((current) => ({ ...current, [field]: event.target.checked }))
                    }
                  />
                  {label}
                </label>
              ))}
            </div>

            {examForm.questions.map((question, index) => (
              <div className="question-card" key={`q-${index + 1}`}>
                <div className="panel-title-row">
                  <strong>Question {index + 1}</strong>
                  <button
                    type="button"
                    className="mini-btn danger"
                    disabled={examForm.questions.length <= 1}
                    onClick={() => removeQuestion(index)}
                  >
                    Remove
                  </button>
                </div>
                <input
                  placeholder="Question text"
                  aria-label={`Question ${index + 1} text`}
                  value={question.question_text}
                  onChange={(event) => updateExamQuestion(index, 'question_text', event.target.value)}
                />
                <div className="inline-fields">
                  <input
                    placeholder="Option A"
                    aria-label={`Question ${index + 1} option A`}
                    value={question.option_a}
                    onChange={(event) => updateExamQuestion(index, 'option_a', event.target.value)}
                  />
                  <input
                    placeholder="Option B"
                    aria-label={`Question ${index + 1} option B`}
                    value={question.option_b}
                    onChange={(event) => updateExamQuestion(index, 'option_b', event.target.value)}
                  />
                </div>
                <div className="inline-fields">
                  <input
                    placeholder="Option C"
                    aria-label={`Question ${index + 1} option C`}
                    value={question.option_c}
                    onChange={(event) => updateExamQuestion(index, 'option_c', event.target.value)}
                  />
                  <input
                    placeholder="Option D"
                    aria-label={`Question ${index + 1} option D`}
                    value={question.option_d}
                    onChange={(event) => updateExamQuestion(index, 'option_d', event.target.value)}
                  />
                </div>
                <div className="inline-fields">
                  <select
                    aria-label={`Question ${index + 1} correct option`}
                    value={question.correct_option}
                    onChange={(event) =>
                      updateExamQuestion(index, 'correct_option', event.target.value)
                    }
                  >
                    <option value="A">Correct A</option>
                    <option value="B">Correct B</option>
                    <option value="C">Correct C</option>
                    <option value="D">Correct D</option>
                  </select>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    aria-label={`Question ${index + 1} marks`}
                    value={question.marks}
                    onChange={(event) => updateExamQuestion(index, 'marks', event.target.value)}
                  />
                </div>
              </div>
            ))}

            {validationError ? (
              <p className="alert-message" role="status" aria-live="polite">
                {validationError}
              </p>
            ) : null}

            <div className="inline-fields">
              <button className="action-btn green" type="button" onClick={addQuestion}>
                Add Question
              </button>
              <button className="action-btn blue" type="submit" disabled={Boolean(validationError)}>
                Save Exam
              </button>
            </div>
          </form>
        </article>

        <article className="white-panel">
          <h2>Bulk Add Exams</h2>
          <p className="helper-text">Paste a JSON payload with an `exams` array.</p>
          <textarea
            rows="20"
            aria-label="Bulk exam JSON"
            value={bulkExamsText}
            onChange={(event) => setBulkExamsText(event.target.value)}
          />
          <button className="action-btn cyan" type="button" onClick={onBulkUpload}>
            Upload Bulk Exams
          </button>
        </article>
      </section>

      <article className="white-panel">
        <h2>Existing Exams ({exams.length})</h2>
        {exams.length ? (
          <div className="data-table">
            <div className="table-row table-head exam-row">
              <span>Title</span>
              <span>Duration</span>
              <span>Questions</span>
              <span>Actions</span>
            </div>
            {exams.map((exam) => (
              <div className="table-row exam-row" key={exam.id}>
                <strong>{exam.title}</strong>
                <span>{exam.duration_minutes} min</span>
                <span>{exam.questions?.length ?? 0}</span>
                <span>
                  <button
                    type="button"
                    className="mini-btn danger"
                    onClick={() => onDeleteExam(exam.id, exam.title)}
                  >
                    Delete
                  </button>
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="helper-text">No exams created yet.</p>
        )}
      </article>
    </section>
  )
}
