export interface ApiUser {
    role: Role
}

export type Role = 'company' | 'applicant' | 'education';