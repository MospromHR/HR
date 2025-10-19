export interface ApiUser {
    role: Role
}

export interface ApiEducationInternship {
    title: string,
    speciality_code: string,
    start_date: string,
    end_date: string,
    capacity: number,
    type: string,
    course: number,
    description: string,
    id: string,
    user_id: string,
    created_at: string,
    updated_at: string
    status: 'draft' | 'published'
}

export interface ApiPayloadVacancies {
    vacancyName: string,
    speciality: string,
    responsibilities: string,
    requirements: string,
    terms: string,
    workSchedule: string,
    workPlace: string,
    map: string,
    probation: string,
    salary: string,
    additionally: string,
    task: string
}
export interface ApiVacancies{
    items: Vacancies[]
}
export interface Vacancies {
    vacancyName: string,
    speciality: string,
    applicationsCount: number,
    responsibilities: string,
    requirements: string,
    terms: string,
    workSchedule: string,
    workPlace: string,
    map: string,
    probation: string,
    salary: string,
    additionally: string,
    task: string,
    id: string,
    companyId: string,
    status:string,
    createdAt: string,
    updatedAt:string,
}

export interface ApiPayloadInternship {
    title: string,
    speciality_code: string,
    start_date: string,
    end_date: string,
    capacity: number,
    type: string,
    course: number
    description: string,
}

export type Role = 'company' | 'applicant' | 'education';