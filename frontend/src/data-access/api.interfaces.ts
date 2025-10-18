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
//{
//     "title": "23",
//     "speciality_code": "23",
//     "start_date": "2025-10-11",
//     "end_date": "2025-11-19",
//     "capacity": 1,
//     "type": "23",
//     "course": 1,
//     "description": "23",
//     "id": "5384c9c0-5c3b-49e0-a54a-2f76531a3296",
//     "user_id": "fcbbc932-1474-4674-ac0d-5f67a8b19da8",
//     "status": "draft",
//     "created_at": "2025-10-18T20:22:13.786446Z",
//     "updated_at": "2025-10-18T20:22:13.786446Z"
// }

export interface ApiInternship {
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