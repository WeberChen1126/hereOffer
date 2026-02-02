export interface User {
  user_id: number;
  email: string;
  user_type: string;
}

export interface Job {
  id: number;
  title: string;
  description: string;
  requirements?: string;
  responsibilities?: string;
  department?: string;
  location?: string;
  salary_range?: string;
  threshold_score: number;
  is_active: boolean;
  created_at: string;
}

export interface Application {
  id: number; // 改为 id
  user_id: number; // 添加 user_id
  job_id: number;
  job_title: string;
  job_description?: string; // 添加 job_description
  status: string;
  resume_text?: string; // 添加 resume_text
  resume_json?: any; // 添加 resume_json
  score_json?: any; // 添加 score_json
  questions_json?: any; // 添加 questions_json
  candidate_email?: string; // 添加 candidate_email (Admin视图)
  created_at: string;
  updated_at?: string; // 添加 updated_at
}

export interface ChatSession {
  session_id: number;
  job_id: number;
  session_type: string;
  created_at: string;
}
