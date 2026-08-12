import { useEffect, useState } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { fetchEvents, fetchAccounts, createEvent, updateEvent, deleteEvent, getGoogleLoginUrl, getMicrosoftLoginUrl } from './api';
import type { UnifiedEvent } from './types';

interface Account {
  key: string;
  provider: string;
  email: string;
  linked: boolean;
}

const accountColors = [
  { bg: '#3B82F6', border: '#2563EB' }, // Blue
  { bg: '#10B981', border: '#059669' }, // Emerald Green
  { bg: '#8B5CF6', border: '#7C3AED' }, // Purple
  { bg: '#F59E0B', border: '#D97706' }, // Amber
  { bg: '#EC4899', border: '#DB2777' }, // Pink
];

function App() {
  const [events, setEvents] = useState<UnifiedEvent[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [eventTitle, setEventTitle] = useState('');
  const [eventDescription, setEventDescription] = useState('');
  const [isAllDay, setIsAllDay] = useState(false);
  const [startDate, setStartDate] = useState<Date | null>(new Date());
  const [endDate, setEndDate] = useState<Date | null>(new Date());
  const [targetAccounts, setTargetAccounts] = useState<string[]>(['all']); 
  const [selectedEventData, setSelectedEventData] = useState<any>(null);

  // Automatically detects the user's local machine timezone (e.g., "Asia/Kolkata")
  const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const loadData = async () => {
    try {
      const [eventData, accountData] = await Promise.all([
        fetchEvents(30),
        fetchAccounts()
      ]);
      setEvents(eventData);
      setAccounts(accountData);
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const colorMap: Record<string, { bg: string; border: string }> = {};
  let colorIndex = 0;

  const getAccountColor = (accountKey: string) => {
    if (!colorMap[accountKey]) {
      colorMap[accountKey] = accountColors[colorIndex % accountColors.length];
      colorIndex++;
    }
    return colorMap[accountKey];
  };

  const handleDateSelect = (selectInfo: any) => {
    setModalMode('create');
    setEventTitle('');
    setEventDescription('');
    setIsAllDay(selectInfo.allDay);
    setStartDate(new Date(selectInfo.startStr));
    setEndDate(new Date(selectInfo.endStr || selectInfo.startStr));
    setTargetAccounts(['all']); 
    setSelectedEventData(selectInfo); 
    setIsModalOpen(true);
  };

  const handleEventClick = (clickInfo: any) => {
    setModalMode('edit');
    setEventTitle(clickInfo.event.title);
    
    const fullEvent = events.find(e => e.id === clickInfo.event.id);
    setEventDescription(fullEvent?.description || '');

    if (fullEvent) {
      const allDayStatus = clickInfo.event.allDay || Boolean(fullEvent.start?.date) || (fullEvent.start?.dateTime?.endsWith('T00:00:00Z') ?? false);
      setIsAllDay(allDayStatus);
      
      const startVal = fullEvent.start?.dateTime || fullEvent.start?.date;
      const endVal = fullEvent.end?.dateTime || fullEvent.end?.date;
      
      setStartDate(startVal ? new Date(startVal) : new Date());
      setEndDate(endVal ? new Date(endVal) : new Date());
      setSelectedEventData(fullEvent);
    }
    
    setIsModalOpen(true);
  };

  const handleEventDrop = async (changeInfo: any) => {
    const updatedEvent = events.find(e => e.id === changeInfo.event.id);
    if (!updatedEvent) return;

    if (!updatedEvent.original_ids || Object.keys(updatedEvent.original_ids).length === 0) {
      console.error("Cannot update event: Missing original_ids mapping.");
      changeInfo.revert();
      return;
    }

    const newStart = changeInfo.event.start.toISOString();
    const newEnd = changeInfo.event.end ? changeInfo.event.end.toISOString() : newStart;

    const payload: UnifiedEvent = {
      ...updatedEvent,
      start: { dateTime: newStart, timeZone: userTimeZone },
      end: { dateTime: newEnd, timeZone: userTimeZone }
    };

    try {
      await updateEvent(updatedEvent.id, payload);
    } catch (error) {
      console.error("Failed to update event time:", error);
      changeInfo.revert(); 
    }
  };

  const formatPayloadDate = (d: Date, allDay: boolean) => {
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    if (allDay) {
      return `${yyyy}-${mm}-${dd}`; 
    }
    return d.toISOString();
  };

  const handleAccountToggle = (key: string) => {
    if (key === 'all') {
      if (targetAccounts.includes('all')) {
        setTargetAccounts([]);
      } else {
        setTargetAccounts(['all']);
      }
      return;
    }

    if (targetAccounts.includes('all')) {
      setTargetAccounts([key]);
      return;
    }

    if (targetAccounts.includes(key)) {
      const updated = targetAccounts.filter(k => k !== key);
      setTargetAccounts(updated.length === 0 ? ['all'] : updated);
    } else {
      setTargetAccounts([...targetAccounts, key]);
    }
  };

  const handleSaveModal = async () => {
    if (!eventTitle.trim() || !startDate || !endDate) return;

    const startStr = formatPayloadDate(startDate, isAllDay);
    const endStr = formatPayloadDate(endDate, isAllDay);

    const startObj = isAllDay ? { date: startStr } : { dateTime: startStr, timeZone: userTimeZone };
    const endObj = isAllDay ? { date: endStr } : { dateTime: endStr, timeZone: userTimeZone };

    if (modalMode === 'create') {
      const calendarApi = selectedEventData.view.calendar;
      calendarApi.unselect(); 

      const newEventPayload: UnifiedEvent = {
        id: `temp_${Date.now()}`, 
        title: eventTitle,
        description: eventDescription,
        start: startObj as any,
        end: endObj as any,
        source: 'unified',
      };

      await createEvent(newEventPayload, targetAccounts);
    } else {
      const updatedPayload: UnifiedEvent = {
        ...selectedEventData,
        title: eventTitle,
        description: eventDescription,
        start: startObj as any,
        end: endObj as any,
      };
      
      try {
        await updateEvent(selectedEventData.id, updatedPayload);
      } catch (error) {
        console.error("Failed to update event:", error);
      }
    }

    setIsModalOpen(false);
    loadData(); 
  };

  const handleDeleteEvent = async () => {
    if (selectedEventData && selectedEventData.original_ids) {
      try {
        await deleteEvent(selectedEventData.id, selectedEventData.original_ids);
        setIsModalOpen(false);
        loadData(); 
      } catch (error) {
        console.error("Failed to delete event:", error);
      }
    } else {
      console.error("Missing original_ids for deletion");
    }
  };

  const calendarEvents = events.map((event) => {
    const accountKey = event.original_ids?.account || event.source;
    const colors = getAccountColor(accountKey);

    const rawStart = event.start?.date || event.start?.dateTime;
    const rawEnd = event.end?.date || event.end?.dateTime;
  
    const isAllDay = Boolean(event.start?.date) || (event.start?.dateTime?.endsWith('T00:00:00Z') ?? false);

    const startDate = isAllDay && rawStart ? rawStart.split('T')[0] : rawStart;
    const endDate = isAllDay && rawEnd ? rawEnd.split('T')[0] : rawEnd;

    return {
      id: event.id,
      title: event.title,
      start: startDate,
      end: endDate,
      allDay: isAllDay,
      backgroundColor: colors.bg,
      borderColor: colors.border,
    };
  });

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <header className="mb-8 bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Unified Calendar View</h1>
          </div>
        </header>

        {/* Main Dashboard Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Left Column: Connected Accounts Sidebar */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 h-fit space-y-6">
            <h2 className="text-lg font-bold text-slate-800 border-b border-gray-100 pb-3">Linked Accounts</h2>
            
            <div className="space-y-3">
              {accounts.map((acc) => {
                const isLinked = acc.linked && !acc.key.includes('placeholder');
                const accColors = isLinked ? getAccountColor(acc.key) : null;

                return (
                  <div key={acc.key} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-gray-100 relative overflow-hidden">
                    {isLinked && (
                      <div className="absolute left-0 top-0 bottom-0 w-1.5" style={{ backgroundColor: accColors?.bg }}></div>
                    )}
                    
                    <div className="overflow-hidden pl-1.5 pr-2">
                      <p className="text-xs font-semibold text-slate-500 uppercase">{acc.provider}</p>
                      <p className="text-sm font-medium text-slate-800 truncate" title={acc.email}>{acc.email}</p>
                    </div>

                    {isLinked ? (
                      <span className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-semibold rounded-full border border-emerald-100 shrink-0">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                        Linked
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 text-gray-500 text-xs font-semibold rounded-full border border-gray-200 shrink-0">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400"></span>
                        Not Linked
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="pt-4 border-t border-gray-100 space-y-3">
              <a href={getGoogleLoginUrl()} className="w-full py-2.5 px-4 bg-white border-2 border-gray-200 hover:border-blue-500 text-slate-700 font-semibold rounded-xl transition-all shadow-sm flex items-center justify-center gap-2 text-sm">
                <div className="w-3 h-3 rounded-full bg-[#4285F4]"></div> Link Google Account
              </a>
              <a href={getMicrosoftLoginUrl()} className="w-full py-2.5 px-4 bg-white border-2 border-gray-200 hover:border-sky-500 text-slate-700 font-semibold rounded-xl transition-all shadow-sm flex items-center justify-center gap-2 text-sm">
                <div className="w-3 h-3 rounded-full bg-[#00A4EF]"></div> Link Microsoft Account
              </a>
            </div>
          </div>

          {/* Right Column: Calendar Grid */}
          <div className="lg:col-span-3 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            {loading ? (
              <div className="flex justify-center items-center h-[700px] text-slate-400 font-medium">Loading calendar events...</div>
            ) : (
              <FullCalendar
                plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                initialView="timeGridWeek"
                headerToolbar={{
                  left: 'prev,next today',
                  center: 'title',
                  right: 'dayGridMonth,timeGridWeek,timeGridDay'
                }}
                events={calendarEvents}
                height="700px"
                slotMinTime="06:00:00"
                slotMaxTime="22:00:00"
                selectable={true}        
                editable={true}          
                select={handleDateSelect} 
                eventClick={handleEventClick}
                eventDrop={handleEventDrop}
                eventResize={handleEventDrop}
              />
            )}
          </div>
        </div>
      </div>

      {/* Modal Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex justify-center items-center z-50">
          <div className="bg-white p-7 rounded-2xl shadow-2xl w-[420px]">
            <h2 className="text-2xl font-bold text-slate-900 mb-6 tracking-tight">
              {modalMode === 'create' ? 'Create New Event' : 'Edit Event'}
            </h2>
            
            <div className="mb-5">
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Event Title</label>
              <input 
                type="text" 
                placeholder="Meeting with Team..." 
                value={eventTitle}
                onChange={(e) => setEventTitle(e.target.value)}
                className="w-full border-2 border-gray-200 rounded-xl p-3 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                autoFocus
              />
            </div>

            <div className="mb-5">
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Description</label>
              <textarea 
                placeholder="Add notes or details..." 
                value={eventDescription}
                onChange={(e) => setEventDescription(e.target.value)}
                rows={3}
                className="w-full border-2 border-gray-200 rounded-xl p-3 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all resize-none text-sm"
              />
            </div>

            {/* Target Account Checkbox Selector (Only shown during creation) */}
            {modalMode === 'create' && (
              <div className="mb-5">
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Target Calendars / Accounts</label>
                <div className="space-y-2 max-h-40 overflow-y-auto border-2 border-gray-200 rounded-xl p-3 bg-white">
                  <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-slate-800 pb-2 border-b border-gray-100">
                    <input 
                      type="checkbox"
                      checked={targetAccounts.includes('all')}
                      onChange={() => handleAccountToggle('all')}
                      className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
                    />
                    🌐 All Linked Accounts
                  </label>
                  
                  {accounts.filter(a => a.linked && !a.key.includes('placeholder')).map(acc => {
                    const isChecked = targetAccounts.includes('all') || targetAccounts.includes(acc.key);
                    return (
                      <label key={acc.key} className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
                        <input 
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleAccountToggle(acc.key)}
                          className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
                        />
                        <span className="truncate">{acc.provider}: {acc.email}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex items-center mb-5">
              <input 
                type="checkbox" 
                id="allDay" 
                checked={isAllDay} 
                onChange={(e) => setIsAllDay(e.target.checked)} 
                className="w-4 h-4 text-blue-600 bg-white border-2 border-gray-300 rounded focus:ring-blue-500 cursor-pointer" 
              />
              <label htmlFor="allDay" className="text-sm font-semibold text-slate-700 ml-2 cursor-pointer select-none">
                All Day Event
              </label>
            </div>

            <div className="flex gap-4 mb-8">
              <div className="flex-1 relative">
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Start</label>
                <div className="relative">
                  <DatePicker
                    selected={startDate}
                    onChange={(date: Date | null) => setStartDate(date)}
                    showTimeSelect={!isAllDay}
                    dateFormat={isAllDay ? "dd-MMM-yyyy" : "dd-MMM-yyyy HH:mm"}
                    className="w-full border-2 border-gray-200 rounded-xl p-2.5 pl-3 pr-10 text-slate-800 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all cursor-pointer"
                    wrapperClassName="w-full"
                    portalId="root"
                    popperPlacement="bottom-start"
                    showPopperArrow={false}
                  />
                  <svg className="w-5 h-5 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
              
              <div className="flex-1 relative">
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">End</label>
                <div className="relative">
                  <DatePicker
                    selected={endDate}
                    onChange={(date: Date | null) => setEndDate(date)}
                    showTimeSelect={!isAllDay}
                    dateFormat={isAllDay ? "dd-MMM-yyyy" : "dd-MMM-yyyy HH:mm"}
                    className="w-full border-2 border-gray-200 rounded-xl p-2.5 pl-3 pr-10 text-slate-800 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all cursor-pointer"
                    wrapperClassName="w-full"
                    portalId="root"
                    popperPlacement="bottom-start"
                    showPopperArrow={false}
                  />
                  <svg className="w-5 h-5 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="flex justify-end items-center gap-2 pt-5 border-t border-gray-100">
              {modalMode === 'edit' && (
                <button onClick={handleDeleteEvent} className="px-4 py-2.5 text-red-600 hover:bg-red-50 rounded-xl font-semibold mr-auto transition-colors">
                  Delete
                </button>
              )}
              <button onClick={() => setIsModalOpen(false)} className="px-5 py-2.5 text-slate-600 hover:text-slate-900 font-semibold transition-colors">
                Cancel
              </button>
              <button onClick={handleSaveModal} className="px-6 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-semibold shadow-sm transition-all">
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;