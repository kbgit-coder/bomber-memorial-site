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
  iwm_name_url?: string;
  ibcc_url?: string;
  bio?: string;
  hometown?: string;
  decorations?: string;
  photo?: string;
}

export interface Source {
  title: string;
  url?: string;
  type?: string;
  still_live?: boolean;
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
  link_description?: string;
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

export type LocationConfidenceStatus = 'verified' | 'confirmed' | 'approximate' | 'estimated';

export interface LocationConfidence {
  status: LocationConfidenceStatus;
  score?: number;
  sources?: string[];
  verified_by?: string;
  verification_date?: string;
  verification_notes?: string;
  community_submissions?: number;
  last_reviewed?: string;
  // Legacy field names (kept for compatibility)
  level?: 'verified' | 'approximate' | 'estimated';
  method?: string;
  notes?: string;
}

export interface RemembranceEvent {
  name: string;
  date?: string;
  description?: string;
}

export interface Remembrance {
  annual_service?: boolean;
  service_date?: string;
  service_description?: string;
  last_known_event?: string;
  events?: RemembranceEvent[];
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
  os_grid_reference?: string;
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
  memorial_details?: string;
  inscription?: string;
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
  community_connection?: string;
  remembrance?: Remembrance;
  last_updated?: string;
  data_quality?: 'Comprehensive' | 'Partial' | 'Stub';
  location_confidence?: LocationConfidence;
  crash_category?: string;
  narrative_quality_score?: number;
  narrative_source?: string;
  squadron_display_name?: string;
  squadron_aliases?: string[];
  documents?: MemorialDocument[];
}

export interface MemorialDocument {
  title: string;
  filename: string;
  description?: string;
  author?: string;
  pages?: number;
}
