export interface CrewMember {
  rank?: string;
  name: string;
  service_number?: string;
  age?: number;
  role?: string;
  nationality?: string;
  fate?: string;
  burial_location?: string;
}

export interface Source {
  title: string;
  url?: string;
  type?: string;
}

export interface Maintainer {
  organisation?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  maintainer_type?: string;
  notes?: string;
}

export interface Memorial {
  id: string;
  title: string;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  county?: string;
  country?: string;
  region_code?: string;
  crash_date?: string;
  aircraft_type?: string;
  serial_number?: string;
  aircraft_code?: string;
  squadron?: string;
  station?: string;
  operation_type?: string;
  operation_target?: string;
  cause_of_loss?: string;
  narrative?: string;
  crew?: CrewMember[];
  crew_summary?: string;
  memorial_type?: string;
  erected_by?: string;
  dedication_date?: string;
  condition?: string;
  maintainer?: Maintainer;
  sources?: Source[];
  contributor?: string;
  last_updated?: string;
  data_quality?: 'Complete' | 'Partial' | 'Stub';
}
