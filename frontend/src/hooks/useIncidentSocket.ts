import { useState, useEffect, useRef, useCallback } from 'react';
import type { Incident } from '../types';
import { WS_URL } from '../services/api';

export function useIncidentSocket(incidentId: string | undefined) {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const connect = useCallback(() => {
    if (!incidentId) return;
    
    // Close existing connection if any
    if (socketRef.current) {
      socketRef.current.close();
    }

    const ws = new WebSocket(`${WS_URL}/ws/incidents/${incidentId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      setConnectionError(false);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        // The backend WebSocket router in FastAPI usually sends the full incident object 
        // or specific event structures.
        if (data.event) {
          // It's an event update
          setIncident(prev => {
            if (!prev) return prev;
            
            const updated = { ...prev };
            const eventData = data.data || {};
            
            if (data.event === 'ETA_UPDATED' && eventData.eta_minutes !== undefined) {
              updated.estimated_response_time_minutes = eventData.eta_minutes;
            } else if (data.event === 'REPLANNING_STARTED') {
              updated.status = 'REPLANNING';
            } else if (data.event === 'REPLANNING_COMPLETED') {
              updated.status = 'IN_PROGRESS';
              if (eventData.eta_minutes !== undefined) {
                updated.estimated_response_time_minutes = eventData.eta_minutes;
              }
            } else if (data.event === 'RESPONDER_ACCEPTED') {
              updated.status = 'ACKNOWLEDGED';
            } else if (data.event === 'RESPONDER_DISPATCHED') {
              updated.status = 'IN_PROGRESS';
            } else if (data.event === 'INCIDENT_RESOLVED') {
              updated.status = 'RESOLVED';
            } else if (data.event === 'AI_ANALYSIS_STARTED') {
              updated.status = 'ANALYZING';
            } else if (data.event === 'AI_ANALYSIS_COMPLETED' || data.event === 'DEPARTMENT_ASSIGNED') {
              if (updated.status === 'REPORTED' || updated.status === 'ANALYZING') {
                updated.status = 'DISPATCHING';
              }
            } else if (data.event === 'INCIDENT_UPDATED' && eventData.incident) {
              return eventData.incident;
            }
            
            const desc = eventData.message || eventData.reason || eventData.description || data.event.replace(/_/g, ' ');
            const timestamp = data.timestamp || new Date().toISOString();

            const existingTimeline = updated.timeline || [];
            const isDuplicate = existingTimeline.some(t => t.event === data.event && t.description === desc);
            
            if (!isDuplicate) {
              const newTimelineEvent = {
                id: (data.timestamp ? new Date(data.timestamp).getTime() : Date.now()).toString(),
                event: data.event,
                description: desc,
                timestamp: timestamp
              };
              updated.timeline = [newTimelineEvent, ...existingTimeline];
            }
            
            return updated;
          });
        } else if (data.id) {
          // It's the full incident object
          setIncident(data);
        }
      } catch (e) {
        console.error('Error parsing WebSocket message', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error', error);
      setConnectionError(true);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
      
      // Auto-reconnect logic
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    };

    socketRef.current = ws;
  }, [incidentId]);

  const fetchIncident = useCallback(async () => {
    if (!incidentId) return false;
    try {
      const response = await fetch(`${WS_URL.replace('ws', 'http')}/api/incidents/${incidentId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setIncident(data);
        return true;
      }
    } catch (e) {
      console.error('Failed to fetch incident', e);
    }
    return false;
  }, [incidentId]);

  useEffect(() => {
    let isSubscribed = true;
    
    const init = async () => {
      await fetchIncident();
      if (isSubscribed) {
        connect();
      }
    };
    
    init();

    return () => {
      isSubscribed = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [fetchIncident, connect]);

  return { incident, setIncident, isConnected, connectionError, fetchIncident };
}
