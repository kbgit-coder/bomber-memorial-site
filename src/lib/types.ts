export interface CrewMember {
  rank?: string;
  name: string;
  service_number?: string;
  age?: number;
  role?: string;
  nationality?: string;
  fate?: string;
  fate_detail?: string;
  burial_location?: string;
  cwgc_url?: string;
  cwgc_verified?: boolean;
  bio?: string;
  hometown?: string;
  decorations?: string;
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

export interface LocalContact {
  org_name: string;
  org_type?: string;
  role?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
}

export interface ExternalNarrative {
  source_site: string;
  original_url: string;
  summary?: string;
  key_details?: string;
  full_narrative?: string;
  date_retrieved?: string;
  still_live?: boolean;
}

export interface Photo {
  filename: string;
  caption?: string;
  source?: string;
  credit?: string;
  date_taken?: string;
}

export interface AdditionalContributor {
  name: string;
  role?: string;
  date?: string;
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
  what3words?: string;
  crash_date?: string;
  aircraft_type?: string;
  serial_number?: string;
  aircraft_code?: string;
  squadron?: string;
  squadron_badge_url?: string;
  squadron_motto?: string;
  station?: string;
  operation_type?: string;
  operation_target?: string;
  cause_of_loss?: string;
  narrative?: string;
  crew?: CrewMember[];
  crew_summary?: string;
  memorial_type?: string;
  memorial_name?: string;
  memorial_address?: string;
  memorial_access_notes?: string;
  erected_by?: string;
  dedication_date?: string;
  condition?: string;
  photos?: Photo[];
  maintainer?: Maintainer;
  local_contacts?: LocalContact[];
  external_narratives?: ExternalNarrative[];
  sources?: Source[];
  contributor?: string;
  additional_contributors?: AdditionalContributor[];
  last_updated?: string;
  data_quality?: 'Complete' | 'Partial' | 'Stub';
}
