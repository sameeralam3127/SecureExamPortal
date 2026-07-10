export default function AssignExam({
  exams,
  students,
  assignmentForm,
  setAssignmentForm,
  onAssign,
  assignments,
  onDeleteAssignment,
}) {
  return (
    <section className="two-grid">
      <article className="white-panel">
        <h2>Assign Exam</h2>
        <form className="form-stack" onSubmit={onAssign}>
          <select
            aria-label="Select exam"
            value={assignmentForm.exam_id}
            onChange={(event) =>
              setAssignmentForm((current) => ({ ...current, exam_id: event.target.value }))
            }
            required
          >
            <option value="">Select exam</option>
            {exams.map((exam) => (
              <option key={exam.id} value={exam.id}>
                {exam.title}
              </option>
            ))}
          </select>
          <select
            aria-label="Select student"
            value={assignmentForm.student_id}
            onChange={(event) =>
              setAssignmentForm((current) => ({ ...current, student_id: event.target.value }))
            }
            required
          >
            <option value="">Select student</option>
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.full_name} ({student.username})
              </option>
            ))}
          </select>
          <button className="action-btn yellow" type="submit">
            Assign Exam
          </button>
        </form>
      </article>
      <article className="white-panel">
        <h2>Current Assignments ({assignments.length})</h2>
        <div className="list-stack">
          {assignments.length ? (
            assignments.map((assignment) => (
              <div className="row-card row-flex" key={assignment.id}>
                <div>
                  <strong>{assignment.exam_title}</strong>
                  <p>
                    {assignment.student_name} | {assignment.attempt_status || 'pending'} | Score{' '}
                    {assignment.latest_score ?? '--'}
                  </p>
                </div>
                <button
                  type="button"
                  className="mini-btn danger"
                  onClick={() => onDeleteAssignment(assignment.id)}
                >
                  Remove
                </button>
              </div>
            ))
          ) : (
            <p className="helper-text">No assignments yet.</p>
          )}
        </div>
      </article>
    </section>
  )
}
