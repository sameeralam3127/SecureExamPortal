import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
const defaultQuestion = {
  question_text: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  correct_option: 'A',
  marks: 1,
}
const userBulkTemplate = `Sameer Student,student2,student2@example.com,student123
Riya Sharma,student3,student3@example.com,student123`
const examBulkTemplate = JSON.stringify(
  {
    exams: [
      {
        title: 'Computer Basics',
        description: 'Introductory MCQ exam',
        duration_minutes: 20,
        questions: [
          {
            question_text: 'CPU stands for?',
            option_a: 'Central Processing Unit',
            option_b: 'Computer Personal Unit',
            option_c: 'Central Power Utility',
            option_d: 'Control Process User',
            correct_option: 'A',
            marks: 2,
          },
        ],
      },
    ],
  },
  null,
  2,
)

function App({ route = '/login', onNavigate = () => {} }) {
  const [session, setSession] = useState(() => {
    const saved = localStorage.getItem('secureExamSession')
    return saved ? JSON.parse(saved) : null
  })
  const [loginForm, setLoginForm] = useState({ username: 'admin', password: 'admin123' })
  const [registerForm, setRegisterForm] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
  })
  const [message, setMessage] = useState('')
  const [activeTab, setActiveTab] = useState('dashboard')

  const [adminStats, setAdminStats] = useState(null)
  const [students, setStudents] = useState([])
  const [exams, setExams] = useState([])
  const [assignments, setAssignments] = useState([])
  const [studentForm, setStudentForm] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
    role: 'student',
  })
  const [bulkUsersText, setBulkUsersText] = useState(userBulkTemplate)
  const [examForm, setExamForm] = useState({
    title: '',
    description: '',
    duration_minutes: 30,
    questions: [{ ...defaultQuestion }],
  })
  const [bulkExamsText, setBulkExamsText] = useState(examBulkTemplate)
  const [assignmentForm, setAssignmentForm] = useState({ exam_id: '', student_id: '' })

  const [studentStats, setStudentStats] = useState(null)
  const [studentAssignments, setStudentAssignments] = useState([])
  const [history, setHistory] = useState([])
  const [liveExam, setLiveExam] = useState(null)
  const [answers, setAnswers] = useState({})
  const [secondsLeft, setSecondsLeft] = useState(0)

  const authHeaders = useMemo(
    () => ({
      'Content-Type': 'application/json',
      Authorization: session?.access_token ? `Bearer ${session.access_token}` : '',
    }),
    [session],
  )

  const apiRequest = async (path, options = {}) => {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { ...authHeaders, ...(options.headers || {}) },
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(data.detail || 'Request failed')
    }
    return data
  }

  const initializeGoogleAuth = () => {
    if (session || route !== '/login' || !GOOGLE_CLIENT_ID || !window.google?.accounts?.id) {
      return false
    }

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: async (response) => {
        try {
          const data = await apiRequest('/api/v1/auth/google', {
            method: 'POST',
            body: JSON.stringify({ credential: response.credential }),
          })
          setSession(data)
          localStorage.setItem('secureExamSession', JSON.stringify(data))
          setMessage('')
        } catch (error) {
          setMessage(error.message)
        }
      },
    })

    const googleButton = document.getElementById('googleSignInButton')
    if (googleButton) {
      googleButton.innerHTML = ''
      window.google.accounts.id.renderButton(googleButton, {
        theme: 'outline',
        size: 'large',
        width: '320',
      })
      return true
    }

    return false
  }

  const loadAdminData = async () => {
    const [statsData, studentsData, examsData, assignmentData] = await Promise.all([
      apiRequest('/api/v1/admin/dashboard'),
      apiRequest('/api/v1/admin/students'),
      apiRequest('/api/v1/admin/exams'),
      apiRequest('/api/v1/admin/assignments'),
    ])
    setAdminStats(statsData)
    setStudents(studentsData)
    setExams(examsData)
    setAssignments(assignmentData)
  }

  const loadStudentData = async () => {
    const [statsData, assignmentData, historyData] = await Promise.all([
      apiRequest('/api/v1/student/dashboard'),
      apiRequest('/api/v1/student/assignments'),
      apiRequest('/api/v1/student/attempts/history'),
    ])
    setStudentStats(statsData)
    setStudentAssignments(assignmentData)
    setHistory(historyData)
  }

  useEffect(() => {
    if (!session) return
    const loader = session.user.role === 'admin' ? loadAdminData : loadStudentData
    loader().catch((error) => setMessage(error.message))
    onNavigate(session.user.role === 'admin' ? '/admin/dashboard' : '/student/dashboard')
  }, [session])

  useEffect(() => {
    if (session || route !== '/login' || !GOOGLE_CLIENT_ID) return

    if (initializeGoogleAuth()) {
      return
    }

    const pollId = window.setInterval(() => {
      if (initializeGoogleAuth()) {
        window.clearInterval(pollId)
      }
    }, 300)

    window.setTimeout(() => window.clearInterval(pollId), 5000)
    return () => window.clearInterval(pollId)
  }, [session, route])

  useEffect(() => {
    if (!liveExam || secondsLeft <= 0) return
    const timerId = window.setInterval(() => {
      setSecondsLeft((value) => Math.max(value - 1, 0))
    }, 1000)
    return () => window.clearInterval(timerId)
  }, [liveExam, secondsLeft])

  useEffect(() => {
    if (liveExam && secondsLeft === 0) {
      submitExam()
    }
  }, [secondsLeft])

  const handleLogin = async (event) => {
    event.preventDefault()
    try {
      const data = await apiRequest('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify(loginForm),
      })
      setSession(data)
      localStorage.setItem('secureExamSession', JSON.stringify(data))
      setActiveTab('dashboard')
      setMessage('')
    } catch (error) {
      setMessage(error.message)
    }
  }

  const logout = () => {
    setSession(null)
    setLiveExam(null)
    setAnswers({})
    setActiveTab('dashboard')
    localStorage.removeItem('secureExamSession')
    onNavigate('/login')
  }

  const handleRegister = async (event) => {
    event.preventDefault()
    try {
      const data = await apiRequest('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify(registerForm),
      })
      setSession(data)
      localStorage.setItem('secureExamSession', JSON.stringify(data))
      setMessage('Registration successful')
      setRegisterForm({ full_name: '', username: '', email: '', password: '' })
    } catch (error) {
      setMessage(error.message)
    }
  }

  const createStudent = async (event) => {
    event.preventDefault()
    try {
      await apiRequest('/api/v1/admin/students', {
        method: 'POST',
        body: JSON.stringify(studentForm),
      })
      setStudentForm({ full_name: '', username: '', email: '', password: '', role: 'student' })
      setMessage('Student created successfully')
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const createStudentsBulk = async () => {
    try {
      const users = bulkUsersText
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const [fullName, username, email, password] = line.split(',').map((item) => item.trim())
          return { full_name: fullName, username, email, password, role: 'student' }
        })

      await apiRequest('/api/v1/admin/students/bulk', {
        method: 'POST',
        body: JSON.stringify({ users }),
      })
      setMessage(`${users.length} students added in bulk`)
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const updateExamQuestion = (index, field, value) => {
    setExamForm((current) => ({
      ...current,
      questions: current.questions.map((question, questionIndex) =>
        questionIndex === index ? { ...question, [field]: value } : question,
      ),
    }))
  }

  const createExam = async (event) => {
    event.preventDefault()
    try {
      await apiRequest('/api/v1/admin/exams', {
        method: 'POST',
        body: JSON.stringify({
          ...examForm,
          duration_minutes: Number(examForm.duration_minutes),
          questions: examForm.questions.map((question) => ({
            ...question,
            marks: Number(question.marks),
          })),
        }),
      })
      setExamForm({
        title: '',
        description: '',
        duration_minutes: 30,
        questions: [{ ...defaultQuestion }],
      })
      setMessage('Exam created successfully')
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const createExamsBulk = async () => {
    try {
      const payload = JSON.parse(bulkExamsText)
      await apiRequest('/api/v1/admin/exams/bulk', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setMessage(`${payload.exams?.length || 0} exams added in bulk`)
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const assignExam = async (event) => {
    event.preventDefault()
    try {
      await apiRequest('/api/v1/admin/assignments', {
        method: 'POST',
        body: JSON.stringify({
          exam_id: Number(assignmentForm.exam_id),
          student_id: Number(assignmentForm.student_id),
        }),
      })
      setAssignmentForm({ exam_id: '', student_id: '' })
      setMessage('Exam assigned successfully')
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const startExam = async (assignmentId) => {
    try {
      const data = await apiRequest(`/api/v1/student/assignments/${assignmentId}/start`, {
        method: 'POST',
      })
      setLiveExam(data)
      setAnswers({})
      setSecondsLeft(data.duration_minutes * 60)
      setActiveTab('exam')
    } catch (error) {
      setMessage(error.message)
    }
  }

  const submitExam = async () => {
    if (!liveExam) return
    try {
      const result = await apiRequest(`/api/v1/student/attempts/${liveExam.attempt_id}/submit`, {
        method: 'POST',
        body: JSON.stringify({
          answers: Object.entries(answers).map(([questionId, selectedOption]) => ({
            question_id: Number(questionId),
            selected_option: selectedOption,
          })),
        }),
      })
      setMessage(`Exam submitted. Score ${result.score}/${result.total_marks} (${result.percentage}%)`)
      setLiveExam(null)
      setAnswers({})
      setSecondsLeft(0)
      setActiveTab('reports')
      loadStudentData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const formatTimer = (value) => {
    const minutes = Math.floor(value / 60)
    const seconds = value % 60
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }

  if (!session) {
    return (
      <main className="login-shell">
        <section className="login-card">
          <div className="brand-mark">🎓 Secure Exam Portal</div>
          <div className="auth-tab-row">
            <button
              type="button"
              className={route !== '/register' ? 'auth-tab active' : 'auth-tab'}
              onClick={() => onNavigate('/login')}
            >
              Login
            </button>
            <button
              type="button"
              className={route === '/register' ? 'auth-tab active' : 'auth-tab'}
              onClick={() => onNavigate('/register')}
            >
              Register
            </button>
          </div>

          {route === '/register' ? (
            <>
              <h1>Create student account</h1>
              <p>Register and you will be redirected to the student dashboard.</p>
              <form className="form-stack" onSubmit={handleRegister}>
                <input
                  value={registerForm.full_name}
                  onChange={(event) =>
                    setRegisterForm((current) => ({
                      ...current,
                      full_name: event.target.value,
                    }))
                  }
                  placeholder="Full name"
                />
                <input
                  value={registerForm.username}
                  onChange={(event) =>
                    setRegisterForm((current) => ({
                      ...current,
                      username: event.target.value,
                    }))
                  }
                  placeholder="Username"
                />
                <input
                  type="email"
                  value={registerForm.email}
                  onChange={(event) =>
                    setRegisterForm((current) => ({ ...current, email: event.target.value }))
                  }
                  placeholder="Email"
                />
                <input
                  type="password"
                  value={registerForm.password}
                  onChange={(event) =>
                    setRegisterForm((current) => ({
                      ...current,
                      password: event.target.value,
                    }))
                  }
                  placeholder="Password"
                />
                {message ? <p className="alert-message">{message}</p> : null}
                <button className="action-btn blue" type="submit">
                  Create Account
                </button>
              </form>
            </>
          ) : (
            <>
              <h1>Login to continue</h1>
              <p>Use demo buttons, password login, or Google sign-in.</p>
              <div className="demo-row">
                <button
                  type="button"
                  onClick={() => setLoginForm({ username: 'admin', password: 'admin123' })}
                >
                  Admin Demo
                </button>
                <button
                  type="button"
                  onClick={() => setLoginForm({ username: 'student1', password: 'student123' })}
                >
                  Student Demo
                </button>
              </div>
              <form className="form-stack" onSubmit={handleLogin}>
                <input
                  value={loginForm.username}
                  onChange={(event) =>
                    setLoginForm((current) => ({ ...current, username: event.target.value }))
                  }
                  placeholder="Username"
                />
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={(event) =>
                    setLoginForm((current) => ({ ...current, password: event.target.value }))
                  }
                  placeholder="Password"
                />
                {message ? <p className="alert-message">{message}</p> : null}
                <button className="action-btn blue" type="submit">
                  Login
                </button>
              </form>
              <div className="google-login-wrap">
                {GOOGLE_CLIENT_ID ? (
                  <div id="googleSignInButton" />
                ) : (
                  <p className="google-disabled">
                    Add <code>VITE_GOOGLE_CLIENT_ID</code> to enable Google login.
                  </p>
                )}
              </div>
            </>
          )}
        </section>
      </main>
    )
  }

  return session.user.role === 'admin'
    ? renderAdminView()
    : renderStudentView()

  function renderAdminView() {
    return (
      <main className="portal-page">
        {renderTopbar(['dashboard', 'exams', 'users', 'reports'])}
        <section className="welcome-banner">
          <div>
            <h1>Welcome, {session.user.full_name}!</h1>
            <p>Here&apos;s what&apos;s happening with your exam portal today.</p>
          </div>
          <span className="prototype-chip">✓ Prototype</span>
        </section>

        <section className="metric-grid">
          <MetricCard color="blue" count={adminStats?.total_students || 0} label="Total Students" icon="👥" />
          <MetricCard color="green" count={adminStats?.total_exams || 0} label="Total Exams" icon="📄" />
          <MetricCard color="cyan" count={adminStats?.total_assignments || 0} label="Active Exams" icon="✓" />
          <MetricCard color="orange" count={adminStats?.completed_attempts || 0} label="Total Results" icon="📊" />
        </section>

        {message ? <div className="notice-bar">{message}</div> : null}

        <section className="white-panel">
          <h2>Quick Actions</h2>
          <div className="quick-grid">
            <button className="action-btn blue" onClick={() => setActiveTab('exams')} type="button">
              + Create New Exam
            </button>
            <button className="action-btn green" onClick={() => setActiveTab('users')} type="button">
              👤 Manage Users
            </button>
            <button className="action-btn cyan" onClick={() => setActiveTab('reports')} type="button">
              📈 View Reports
            </button>
            <button className="action-btn yellow" onClick={() => setActiveTab('exams')} type="button">
              ☰ Manage Exams
            </button>
          </div>
        </section>

        {activeTab === 'dashboard' && (
          <section className="three-grid">
            <MiniCard
              title="Upcoming Exams"
              text={`${assignments.filter((item) => item.attempt_status !== 'submitted').length} pending assigned exams.`}
              buttonText="View Schedule"
              onClick={() => setActiveTab('exams')}
            />
            <MiniCard
              title="Previous Results"
              text={`Average result score is ${adminStats?.average_score || 0}%.`}
              buttonText="View Results"
              onClick={() => setActiveTab('reports')}
            />
            <MiniCard
              title="Profile"
              text={`Logged in as ${session.user.username}.`}
              buttonText="Manage Users"
              onClick={() => setActiveTab('users')}
            />
          </section>
        )}

        {activeTab === 'users' && (
          <section className="two-grid">
            <article className="white-panel">
              <h2>Add Single Student</h2>
              <form className="form-stack" onSubmit={createStudent}>
                <input
                  placeholder="Full name"
                  value={studentForm.full_name}
                  onChange={(event) =>
                    setStudentForm((current) => ({ ...current, full_name: event.target.value }))
                  }
                />
                <input
                  placeholder="Username"
                  value={studentForm.username}
                  onChange={(event) =>
                    setStudentForm((current) => ({ ...current, username: event.target.value }))
                  }
                />
                <input
                  placeholder="Email"
                  type="email"
                  value={studentForm.email}
                  onChange={(event) =>
                    setStudentForm((current) => ({ ...current, email: event.target.value }))
                  }
                />
                <input
                  placeholder="Password"
                  type="password"
                  value={studentForm.password}
                  onChange={(event) =>
                    setStudentForm((current) => ({ ...current, password: event.target.value }))
                  }
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
                value={bulkUsersText}
                onChange={(event) => setBulkUsersText(event.target.value)}
              />
              <button className="action-btn green" type="button" onClick={createStudentsBulk}>
                Upload Bulk Students
              </button>
            </article>
          </section>
        )}

        {activeTab === 'exams' && (
          <section className="two-grid">
            <article className="white-panel">
              <h2>Create Exam</h2>
              <form className="form-stack" onSubmit={createExam}>
                <div className="inline-fields">
                  <input
                    placeholder="Exam title"
                    value={examForm.title}
                    onChange={(event) => setExamForm((current) => ({ ...current, title: event.target.value }))}
                  />
                  <input
                    type="number"
                    min="1"
                    value={examForm.duration_minutes}
                    onChange={(event) =>
                      setExamForm((current) => ({ ...current, duration_minutes: event.target.value }))
                    }
                  />
                </div>
                <textarea
                  placeholder="Description"
                  value={examForm.description}
                  onChange={(event) =>
                    setExamForm((current) => ({ ...current, description: event.target.value }))
                  }
                />
                {examForm.questions.map((question, index) => (
                  <div className="question-card" key={`q-${index + 1}`}>
                    <input
                      placeholder={`Question ${index + 1}`}
                      value={question.question_text}
                      onChange={(event) => updateExamQuestion(index, 'question_text', event.target.value)}
                    />
                    <div className="inline-fields">
                      <input
                        placeholder="Option A"
                        value={question.option_a}
                        onChange={(event) => updateExamQuestion(index, 'option_a', event.target.value)}
                      />
                      <input
                        placeholder="Option B"
                        value={question.option_b}
                        onChange={(event) => updateExamQuestion(index, 'option_b', event.target.value)}
                      />
                    </div>
                    <div className="inline-fields">
                      <input
                        placeholder="Option C"
                        value={question.option_c}
                        onChange={(event) => updateExamQuestion(index, 'option_c', event.target.value)}
                      />
                      <input
                        placeholder="Option D"
                        value={question.option_d}
                        onChange={(event) => updateExamQuestion(index, 'option_d', event.target.value)}
                      />
                    </div>
                    <div className="inline-fields">
                      <select
                        value={question.correct_option}
                        onChange={(event) => updateExamQuestion(index, 'correct_option', event.target.value)}
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
                        value={question.marks}
                        onChange={(event) => updateExamQuestion(index, 'marks', event.target.value)}
                      />
                    </div>
                  </div>
                ))}
                <div className="inline-fields">
                  <button
                    className="action-btn green"
                    type="button"
                    onClick={() =>
                      setExamForm((current) => ({
                        ...current,
                        questions: [...current.questions, { ...defaultQuestion }],
                      }))
                    }
                  >
                    Add Question
                  </button>
                  <button className="action-btn blue" type="submit">
                    Save Exam
                  </button>
                </div>
              </form>
            </article>

            <article className="white-panel">
              <h2>Bulk Add Exams</h2>
              <p className="helper-text">Paste JSON payload with an `exams` array.</p>
              <textarea
                rows="20"
                value={bulkExamsText}
                onChange={(event) => setBulkExamsText(event.target.value)}
              />
              <button className="action-btn cyan" type="button" onClick={createExamsBulk}>
                Upload Bulk Exams
              </button>
            </article>
          </section>
        )}

        {activeTab === 'reports' && (
          <section className="two-grid">
            <article className="white-panel">
              <h2>Assign Exam</h2>
              <form className="form-stack" onSubmit={assignExam}>
                <select
                  value={assignmentForm.exam_id}
                  onChange={(event) =>
                    setAssignmentForm((current) => ({ ...current, exam_id: event.target.value }))
                  }
                >
                  <option value="">Select exam</option>
                  {exams.map((exam) => (
                    <option key={exam.id} value={exam.id}>
                      {exam.title}
                    </option>
                  ))}
                </select>
                <select
                  value={assignmentForm.student_id}
                  onChange={(event) =>
                    setAssignmentForm((current) => ({ ...current, student_id: event.target.value }))
                  }
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
              <h2>Assignment & Score Report</h2>
              <div className="list-stack">
                {assignments.map((assignment) => (
                  <div className="row-card" key={assignment.id}>
                    <strong>{assignment.exam_title}</strong>
                    <p>
                      {assignment.student_name} | {assignment.attempt_status || 'pending'} | Score{' '}
                      {assignment.latest_score ?? '--'}
                    </p>
                  </div>
                ))}
              </div>
            </article>
          </section>
        )}
      </main>
    )
  }

  function renderStudentView() {
    return (
      <main className="portal-page">
        {renderTopbar(['dashboard', 'exam', 'reports'])}
        <section className="welcome-banner">
          <div>
            <h1>Welcome, {session.user.full_name}!</h1>
            <p>Track assigned exams, take live assessments, and review your scores.</p>
          </div>
          <span className="prototype-chip">Student Portal</span>
        </section>

        <section className="metric-grid">
          <MetricCard color="blue" count={studentStats?.assigned_exams || 0} label="Assigned Exams" icon="📘" />
          <MetricCard color="green" count={studentStats?.completed_exams || 0} label="Completed" icon="✅" />
          <MetricCard color="cyan" count={studentStats?.pending_exams || 0} label="Pending" icon="⏳" />
          <MetricCard color="orange" count={`${studentStats?.average_score || 0}%`} label="Average Score" icon="📊" />
        </section>

        {message ? <div className="notice-bar">{message}</div> : null}

        {activeTab === 'dashboard' && (
          <section className="three-grid">
            <MiniCard
              title="Upcoming Exams"
              text={`${studentAssignments.filter((item) => item.status !== 'submitted').length} exams pending.`}
              buttonText="View Schedule"
              onClick={() => setActiveTab('exam')}
            />
            <MiniCard
              title="Previous Results"
              text="View your past exam results and performance."
              buttonText="View Results"
              onClick={() => setActiveTab('reports')}
            />
            <MiniCard
              title="Profile"
              text={`Username: ${session.user.username}`}
              buttonText="Dashboard"
              onClick={() => setActiveTab('dashboard')}
            />
          </section>
        )}

        {activeTab === 'exam' && (
          liveExam ? (
            <section className="white-panel">
              <div className="exam-header">
                <div>
                  <h2>{liveExam.title}</h2>
                  <p className="helper-text">{liveExam.description}</p>
                </div>
                <div className={`timer-pill ${secondsLeft < 60 ? 'urgent' : ''}`}>{formatTimer(secondsLeft)}</div>
              </div>
              <div className="list-stack">
                {liveExam.questions.map((question, index) => (
                  <div className="question-card" key={question.id}>
                    <strong>
                      {index + 1}. {question.question_text}
                    </strong>
                    {['A', 'B', 'C', 'D'].map((optionKey) => (
                      <label className="option-choice" key={`${question.id}-${optionKey}`}>
                        <input
                          type="radio"
                          name={`question-${question.id}`}
                          checked={answers[question.id] === optionKey}
                          onChange={() =>
                            setAnswers((current) => ({ ...current, [question.id]: optionKey }))
                          }
                        />
                        <span>
                          {optionKey}. {question[`option_${optionKey.toLowerCase()}`]}
                        </span>
                      </label>
                    ))}
                  </div>
                ))}
              </div>
              <button className="action-btn blue" type="button" onClick={submitExam}>
                Submit Exam
              </button>
            </section>
          ) : (
            <section className="white-panel">
              <h2>Assigned Exams</h2>
              <div className="list-stack">
                {studentAssignments.map((assignment) => (
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
                      onClick={() => startExam(assignment.assignment_id)}
                    >
                      {assignment.status === 'in_progress' ? 'Resume' : 'Start'}
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )
        )}

        {activeTab === 'reports' && (
          <section className="white-panel">
            <h2>Score History</h2>
            <div className="list-stack">
              {history.map((attempt) => (
                <div className="row-card" key={attempt.attempt_id}>
                  <strong>{attempt.exam_title}</strong>
                  <p>
                    Score {attempt.score}/{attempt.total_marks} | {attempt.percentage}% | {attempt.status}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    )
  }

  function renderTopbar(tabs) {
    return (
      <header className="portal-navbar">
        <div className="brand-area">🎓 Secure Exam Portal</div>
        <nav className="nav-links">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              className={activeTab === tab ? 'nav-active' : ''}
              onClick={() => {
                setActiveTab(tab)
                if (tab !== 'exam' && liveExam) {
                  setActiveTab('exam')
                }
              }}
            >
              {tab === 'dashboard' && '◔ Dashboard'}
              {tab === 'exams' && '📄 Exams'}
              {tab === 'users' && '👥 Users'}
              {tab === 'reports' && '📈 Reports'}
              {tab === 'exam' && '📝 Exams'}
            </button>
          ))}
          <button type="button" className="logout-btn" onClick={logout}>
            ⟲ Logout
          </button>
        </nav>
      </header>
    )
  }
}

function MetricCard({ color, count, label, icon }) {
  return (
    <article className={`metric-card ${color}`}>
      <div>
        <h3>{count}</h3>
        <p>{label}</p>
      </div>
      <span className="metric-icon">{icon}</span>
    </article>
  )
}

function MiniCard({ title, text, buttonText, onClick }) {
  return (
    <article className="white-panel mini-card">
      <h2>{title}</h2>
      <p className="helper-text">{text}</p>
      <button className="mini-btn" type="button" onClick={onClick}>
        {buttonText}
      </button>
    </article>
  )
}

export default App
