from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from database import supabase
from dependencies import get_college_id, get_current_user
from auto_handler import AutoHandler

router = APIRouter(prefix="/substitution", tags=["Substitution Engine"])

class SubstitutionAssign(BaseModel):
    leave_id: int
    slot_id: int
    substitute_faculty_id: int

@router.post("/find/{leave_id}")
async def find_substitution(
    leave_id: int, 
    college_id: str = Depends(get_college_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Find substitutes for ALL affected slots of a leave request.
    Uses Auto Handler's 5 rules for each slot.
    """
    try:
        # Get leave details
        leave_res = supabase.table("leave_requests").select("*").eq("id", leave_id).eq("college_id", college_id).execute()
        if not leave_res.data:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        leave = leave_res.data[0]
        
        # Use Auto Handler to find substitutes for all slots
        handler = AutoHandler(college_id)
        result = handler.find_substitutes_for_leave(leave)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding substitution: {str(e)}")

@router.post("/assign")
async def assign_substitute(
    data: SubstitutionAssign,
    college_id: str = Depends(get_college_id),
    current_user: dict = Depends(get_current_user)
):
    """Assign a substitute to a specific timetable slot affected by leave."""
    if current_user["role"] not in ["admin", "hod", "superadmin"]:
        raise HTTPException(status_code=403, detail="Only admin or HOD can assign substitutes")
    
    try:
        # Verify leave and slot belong to this college
        leave_res = supabase.table("leave_requests").select("id, faculty_id, leave_date").eq("id", data.leave_id).eq("college_id", college_id).execute()
        if not leave_res.data:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        slot_res = supabase.table("timetable_slots").select("*").eq("id", data.slot_id).eq("college_id", college_id).execute()
        if not slot_res.data:
            raise HTTPException(status_code=404, detail="Timetable slot not found")
        
        slot = slot_res.data[0]
        leave = leave_res.data[0]
        
        # Create substitution record
        sub_data = {
            "college_id": college_id,
            "leave_request_id": data.leave_id,
            "original_faculty_id": leave["faculty_id"],
            "substitute_faculty_id": data.substitute_faculty_id,
            "timetable_slot_id": data.slot_id,
            "date": leave["leave_date"],
            "status": "pending",
            "priority": 1,
            "auto_assigned": False
        }
        
        result = supabase.table("substitutions").insert(sub_data).execute()
        
        return {
            "message": "Substitute assigned to slot successfully",
            "substitution_id": result.data[0]["id"] if result.data else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning substitute: {str(e)}")

@router.post("/confirm/{substitution_id}")
async def confirm_substitution(
    substitution_id: int,
    college_id: str = Depends(get_college_id),
    current_user: dict = Depends(get_current_user)
):
    """Confirm a substitution and trigger notifications."""
    if current_user["role"] not in ["admin", "hod", "superadmin"]:
        raise HTTPException(status_code=403, detail="Only admin or HOD can confirm substitutions")
    
    try:
        # Get substitution
        sub_res = supabase.table("substitutions").select("*").eq("id", substitution_id).eq("college_id", college_id).execute()
        if not sub_res.data:
            raise HTTPException(status_code=404, detail="Substitution not found")
        
        substitution = sub_res.data[0]
        substitution["confirmed_by"] = current_user["id"]
        
        # Use Auto Handler to process confirmation
        handler = AutoHandler(college_id)
        result = handler.process_substitution_confirmation(substitution)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error confirming substitution: {str(e)}")

@router.get("/log")
async def get_substitution_log(
    college_id: str = Depends(get_college_id),
    current_user: dict = Depends(get_current_user)
):
    """Get substitution history/log enriched with faculty and slot info."""
    try:
        res = supabase.table("substitutions").select("*").eq("college_id", college_id).order("requested_at", desc=True).execute()
        
        if not res.data:
            return {"substitutions": []}
            
        # Enrich with faculty names
        all_faculty_ids = list(set([s["original_faculty_id"] for s in res.data] + [s["substitute_faculty_id"] for s in res.data]))
        faculty_map = {}
        if all_faculty_ids:
            fac_res = supabase.table("faculty").select("id, name").in_("id", all_faculty_ids).execute()
            faculty_map = {f["id"]: f["name"] for f in fac_res.data}
            
        # Enrich with slot info
        slot_ids = list(set([s["timetable_slot_id"] for s in res.data]))
        slot_map = {}
        if slot_ids:
            slots_res = supabase.table("timetable_slots").select("id, start_time, end_time, day").in_("id", slot_ids).execute()
            slot_map = {s["id"]: s for s in slots_res.data}
        
        log = []
        for s in res.data:
            slot_info = slot_map.get(s["timetable_slot_id"], {})
            log.append({
                "id": s["id"],
                "original_faculty_name": faculty_map.get(s["original_faculty_id"], "Unknown"),
                "substitute_faculty_name": faculty_map.get(s["substitute_faculty_id"], "Unknown"),
                "date": s["date"],
                "time": f"{slot_info.get('start_time')} - {slot_info.get('end_time')}" if slot_info else "Unknown",
                "status": s["status"],
                "requested_at": s.get("requested_at")
            })
        
        return {"substitutions": log}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching substitution log: {str(e)}")

@router.get("/pending")
async def get_pending_substitutions(
    college_id: str = Depends(get_college_id),
    current_user: dict = Depends(get_current_user)
):
    """Get pending substitutions for the admin dashboard."""
    try:
        res = supabase.table("substitutions").select("*").eq("college_id", college_id).eq("status", "pending").order("requested_at", desc=True).execute()
        
        if not res.data:
            return {"pending_substitutions": []}
            
        # Enrich
        faculty_ids = list(set([s["original_faculty_id"] for s in res.data] + [s["substitute_faculty_id"] for s in res.data]))
        faculty_map = {}
        if faculty_ids:
            fac_res = supabase.table("faculty").select("id, name").in_("id", faculty_ids).execute()
            faculty_map = {f["id"]: f for f in fac_res.data}
            
        slot_ids = list(set([s["timetable_slot_id"] for s in res.data]))
        slot_map = {}
        if slot_ids:
            slots_res = supabase.table("timetable_slots").select("id, start_time, end_time").in_("id", slot_ids).execute()
            slot_map = {s["id"]: s for s in slots_res.data}
        
        pending = []
        for s in res.data:
            orig_name = faculty_map.get(s["original_faculty_id"], {}).get("name", "Unknown")
            sub_name = faculty_map.get(s["substitute_faculty_id"], {}).get("name", "Unknown")
            slot = slot_map.get(s["timetable_slot_id"], {})
            
            pending.append({
                "id": s["id"],
                "original_faculty": orig_name,
                "substitute_faculty": sub_name,
                "date": s["date"],
                "time": f"{slot.get('start_time')} - {slot.get('end_time')}" if slot else "N/A",
                "requested_at": s.get("requested_at")
            })
        
        return {"pending_substitutions": pending}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pending substitutions: {str(e)}")
