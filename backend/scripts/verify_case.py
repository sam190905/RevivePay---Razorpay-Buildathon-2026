import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import engine
from app.models.recovery_case import RecoveryCase
from app.models.audit_log import AuditLog
from app.models.payment import Payment

async def verify():
    async with AsyncSession(engine) as session:
        # Get latest case
        stmt = select(RecoveryCase).order_by(RecoveryCase.opened_at.desc()).limit(1)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()
        
        if not case:
            print("No cases found!")
            return
            
        print(f"Case ID: {case.id}")
        
        # Get audit logs for this case
        stmt = select(AuditLog).where(AuditLog.recovery_case_id == case.id).order_by(AuditLog.timestamp)
        result = await session.execute(stmt)
        logs = result.scalars().all()
        
        print("\nAudit Timeline:")
        for log in logs:
            print(f"[{log.event_type}] Actor: {log.actor} | Action: {log.action}")
            if log.event_type == 'ai_diagnosis':
                meta = log.metadata_json
                print(f"  Classification: {meta.get('classification')}")
                print(f"  Confidence: {meta.get('confidence')}")
                print(f"  Recommended Action: {meta.get('recommended_action')}")
                print(f"  Reason: {meta.get('reason')}")
            if log.event_type == 'policy_check':
                meta = log.metadata_json
                print(f"  Outcome: {meta.get('outcome')} | Action: {meta.get('action')}")
                
if __name__ == "__main__":
    asyncio.run(verify())
