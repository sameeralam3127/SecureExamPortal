import { useMemo, useState } from 'react'

export default function ManageUsers({
  students,
  studentForm,
  setStudentForm,
  onCreateStudent,
  onDeleteStudent,
  bulkUsersText,
  setBulkUsersText,
  onBulkUpload,
}) {
  const [search, setSearch] = useState('')

  const filteredStudents = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return students
    return students.filter((student) =>
      [student.full_name, student.username, student.email]
        .filter(Boolean)
        .some((field) => field.toLowerCase().includes(term)),
    )
  }, [students, search])

  return (
    <section className="admin-stack">
      <article className="white-panel">
        <div className="panel-title-row">
          <h2>Students ({students.length})</h2>
          <input
            type="search"
            className="inline-search"
            placeholder="Search by name, username, or email"
            aria-label="Search students"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        {filteredStudents.length ? (
          <div className="data-table user-table">
            <div className="table-row table-head">
              <span>Name</span>
              <span>Username</span>
              <span>Email</span>
              <span>Actions</span>
            </div>
            {filteredStudents.map((student) => (
              <div className="table-row" key={student.id}>
                <strong>{student.full_name}</strong>
                <span>@{student.username}</span>
                <span className="ellipsis" title={student.email}>
                  {student.email}
                </span>
                <span>
                  <button
                    type="button"
                    className="mini-btn danger"
                    onClick={() => onDeleteStudent(student.id, student.full_name)}
                  >
                    Delete
                  </button>
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="helper-text">
            {students.length ? 'No students match your search.' : 'No students yet. Add one below.'}
          </p>
        )}
      </article>

      <section className="two-grid">
        <article className="white-panel">
          <h2>Add Single Student</h2>
          <form className="form-stack" onSubmit={onCreateStudent}>
            <input
              placeholder="Full name"
              aria-label="Full name"
              value={studentForm.full_name}
              onChange={(event) =>
                setStudentForm((current) => ({ ...current, full_name: event.target.value }))
              }
              required
            />
            <input
              placeholder="Username"
              aria-label="Username"
              value={studentForm.username}
              onChange={(event) =>
                setStudentForm((current) => ({ ...current, username: event.target.value }))
              }
              required
              minLength={3}
            />
            <input
              placeholder="Email"
              aria-label="Email"
              type="email"
              value={studentForm.email}
              onChange={(event) =>
                setStudentForm((current) => ({ ...current, email: event.target.value }))
              }
              required
            />
            <input
              placeholder="Password (min 8 chars, letters and numbers)"
              aria-label="Password"
              type="password"
              value={studentForm.password}
              onChange={(event) =>
                setStudentForm((current) => ({ ...current, password: event.target.value }))
              }
              required
              minLength={8}
            />
            <button className="action-btn blue" type="submit">
              Save Student
            </button>
          </form>
        </article>

        <article className="white-panel">
          <h2>Bulk Add Students</h2>
          <p className="helper-text">One row per student: Full Name, Username, Email, Password</p>
          <textarea
            rows="8"
            aria-label="Bulk student rows"
            value={bulkUsersText}
            onChange={(event) => setBulkUsersText(event.target.value)}
          />
          <button className="action-btn green" type="button" onClick={onBulkUpload}>
            Upload Bulk Students
          </button>
        </article>
      </section>
    </section>
  )
}
