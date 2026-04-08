from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.data.tables import get_db
from app.routers.schemas import ReportCreate, ReportResponse
from app.ai.analysis import Analysis 

router = APIRouter(prefix="/api/baseline", tags=["Baseline"])
@router.post("/record")
def record_baseline(
    report_data: ReportCreate, 
    db: Session = Depends(get_db)
):
    analyzer = Analysis(db)
    try:
        new_report = analyzer.generate_report(report_data)
        analyzer.set_baseline(report_id=new_report.id, user_id=report_data.user_id)
        return {
            "status": "success",
            "message": "Baseline successfully recorded",
            "baseline_id": new_report.id,
            "report_summary": {
                "gvi": new_report.gvi_score,
                "score": new_report.overall_score,
                "ai_verdict": new_report.status
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/{user_id}")
def get_user_baseline(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profiles).filter(Profiles.id == user_id).first()
    
    if not profile or not profile.baseline_report_id:
        return {
            "has_baseline": False, 
            "message": "Baseline not recorded yet. Please use /api/baseline/record first."
        }
    
    baseline = profile.baseline_report 
    
    return {
        "has_baseline": True,
        "baseline_info": {
            "report_id": baseline.id,
            "recorded_at": baseline.created_at.isoformat(),
            "activity_type": baseline.activity_type,
            "overall_score": baseline.overall_score
        },
        "metrics": {
            "rhythm_pace": {
                "cadence": baseline.rhythm_pace.get("cadence"),
                "avg_speed": baseline.rhythm_pace.get("avg_speed"),
                "avg_step_length": baseline.rhythm_pace.get("avg_step_length"),
                "avg_stride_time": baseline.rhythm_pace.get("avg_stride_time")
            },
            "joint_mechanics": {
                "knee_rom": baseline.joint_mechanics.get("knee_angle", {}).get("amplitude"),
                "hip_rom": baseline.joint_mechanics.get("hip_angle", {}).get("amplitude"),
                "knee_mean": baseline.joint_mechanics.get("knee_angle", {}).get("mean"),
                "hip_mean": baseline.joint_mechanics.get("hip_angle", {}).get("mean")
            },
            "variability": {
                "gvi": baseline.gvi_score,
                "step_time_variability": baseline.variability.get("step_time_variability"),
                "knee_angle_variability": baseline.variability.get("knee_angle_variability"),
                "stride_length_variability": baseline.variability.get("stride_length_variability")
            },
            "symmetry_phases": {
                "stance_swing_ratio": baseline.symmetry_phases.get("stance_swing_ratio"),
                "avg_impact_force": baseline.symmetry_phases.get("avg_impact_force"),
                "double_support_time": baseline.symmetry_phases.get("double_support_time"),
                "avg_stance_time": baseline.symmetry_phases.get("avg_stance_time"),
                "avg_swing_time": baseline.symmetry_phases.get("avg_swing_time")
            }
        },
        "clinical_context": {
            "status": baseline.status,
            "narrative": baseline.clinical_narrative,
            "recommendations": baseline.recommendations
        }
    }