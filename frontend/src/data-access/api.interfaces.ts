export interface ApiUser {
    role: Role
}

export interface ApiEducationInternship {
    title: string,
    speciality_code: string,
    start_date: string,
    end_date: string,
    capacity: number,
    id: string,
    user_id: string,
    created_at: string,
    updated_at: string
}

export interface ApiInternship {
    title: string,
    speciality_code: string,
    start_date: string,
    end_date: string,
    capacity: number,
}

export type Role = 'company' | 'applicant' | 'education';