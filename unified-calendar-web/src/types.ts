export interface EventDateTime {
  dateTime: string;
  date?: string;
  timeZone: string;
}

export interface UnifiedEvent {
  id: string;
  title: string;
  description?: string;
  start: EventDateTime;
  end: EventDateTime;
  source: 'google' | 'microsoft' | 'unified';
  original_ids?: Record<string, string>;
}