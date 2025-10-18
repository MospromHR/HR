export interface InternshipCell {
    id: string,
    period: string,
    type: string,
    course: number,
    capacity: number,
    description: string,
    status: 'draft' | 'published'
}