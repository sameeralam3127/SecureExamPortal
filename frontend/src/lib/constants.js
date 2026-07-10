export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

export const defaultQuestion = {
  question_text: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  correct_option: 'A',
  marks: 1,
}

export const emptyExamForm = () => ({
  title: '',
  description: '',
  duration_minutes: 30,
  block_clipboard: true,
  block_context_menu: true,
  block_inspect_shortcuts: true,
  enforce_fullscreen: false,
  track_focus_loss: true,
  questions: [{ ...defaultQuestion }],
})

export const emptyStudentForm = () => ({
  full_name: '',
  username: '',
  email: '',
  password: '',
  role: 'student',
})

export const userBulkTemplate = 'Full Name,username,email,password'

export const examBulkTemplate = JSON.stringify(
  {
    exams: [
      {
        title: 'Computer Basics',
        description: 'Introductory MCQ exam',
        duration_minutes: 20,
        block_clipboard: true,
        block_context_menu: true,
        block_inspect_shortcuts: true,
        enforce_fullscreen: false,
        track_focus_loss: true,
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
