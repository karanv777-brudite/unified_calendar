export interface EventDateTime {
  dateTime?: string;
  date?: string;
  timeZone?: string;
}

export interface Attendee{
  email: string;
  status?: 'pending' | 'accepted' | 'declined';
}

export interface UnifiedEvent {
  id: string;
  title: string;
  description?: string;
  start: EventDateTime;
  end: EventDateTime;
  source: 'google' | 'microsoft' | 'unified' | 'invite';
  original_ids?: Record<string, string>;
  attendees?: Attendee[];
}

export interface Account {
  key: string;
  provider: string;
  email: string;
  linked: boolean;
}