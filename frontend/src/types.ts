export type DepartmentName = 'NONE' | 'MEDICAL' | 'SECURITY' | 'TRANSPORT' | 'FACILITIES' | 'COMMUNICATION';

export interface User {
  id: string;
  name: string;
  email: string;
  department: DepartmentName;
}

export type IncidentStatus = 
  | 'REPORTED' 
  | 'ANALYZING'
  | 'WAITING_FOR_APPROVAL'
  | 'DISPATCHING' 
  | 'ACKNOWLEDGED' 
  | 'IN_PROGRESS' 
  | 'REPLANNING' 
  | 'RESOLVED' 
  | 'CANCELLED';

export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface TimelineEvent {
  id: string;
  event: string;
  description: string;
  timestamp: string;
}

export interface Incident {
  id: string;
  reporter_id?: string;
  title?: string;
  description: string;
  incident_type?: string;
  status: IncidentStatus;
  severity?: Severity;
  location_name?: string;
  estimated_response_time_minutes?: number;
  immediate_guidance?: string;
  created_at: string;
  updated_at?: string;
  timeline: TimelineEvent[];
}
