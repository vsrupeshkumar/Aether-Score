"""
Team score service for DAO/organization team score aggregation
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger
from services.scoring import ScoringService
from services.referral_service import ReferralService

logger = get_logger(__name__)


class TeamScoreService:
    """Service for managing team scores"""
    
    # Minimum members required for team score
    MIN_TEAM_MEMBERS = 3
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.referral_service = ReferralService()
    
    async def create_team(
        self,
        team_name: str,
        admin_address: str,
        member_addresses: Optional[List[str]] = None,
        team_type: str = 'custom',
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Create DAO/organization team
        
        Args:
            team_name: Team name
            admin_address: Admin wallet address
            member_addresses: Optional list of member addresses
            team_type: Team type ('dao', 'organization', 'custom')
            session: Database session (optional)
            
        Returns:
            Created team dict
        """
        try:
            from database.connection import get_session
            from database.models import Team, TeamMember
            
            if session is None:
                async with get_session() as db_session:
                    return await self._create_team(
                        team_name, admin_address, member_addresses, team_type, db_session
                    )
            else:
                return await self._create_team(
                    team_name, admin_address, member_addresses, team_type, session
                )
        except Exception as e:
            logger.error(f"Error creating team: {e}", exc_info=True)
            return None
    
    async def _create_team(
        self,
        team_name: str,
        admin_address: str,
        member_addresses: Optional[List[str]],
        team_type: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Create team in database"""
        from database.models import Team, TeamMember
        
        try:
            # Create team
            team = Team(
                team_name=team_name,
                team_type=team_type,
                admin_address=admin_address
            )
            session.add(team)
            await session.flush()  # Get team ID
            
            # Add admin as member
            admin_member = TeamMember(
                team_id=team.id,
                wallet_address=admin_address,
                role='admin'
            )
            session.add(admin_member)
            
            # Add other members if provided
            if member_addresses:
                for member_address in member_addresses:
                    if member_address.lower() != admin_address.lower():
                        member = TeamMember(
                            team_id=team.id,
                            wallet_address=member_address,
                            role='member'
                        )
                        session.add(member)
            
            await session.commit()
            
            logger.info(f"Created team {team_name} (ID: {team.id}) with admin {admin_address}")
            
            return {
                "id": team.id,
                "team_name": team_name,
                "team_type": team_type,
                "admin_address": admin_address,
                "member_count": len(member_addresses) + 1 if member_addresses else 1,
                "created_at": team.created_at.isoformat() if team.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _create_team: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def add_team_member(
        self,
        team_id: int,
        member_address: str,
        admin_address: str,
        session=None
    ) -> bool:
        """
        Add member to team
        
        Args:
            team_id: Team ID
            member_address: Member wallet address
            admin_address: Admin address (for authorization)
            session: Database session (optional)
            
        Returns:
            True if added successfully
        """
        try:
            from database.connection import get_session
            from database.models import Team, TeamMember
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._add_team_member(team_id, member_address, admin_address, db_session)
            else:
                return await self._add_team_member(team_id, member_address, admin_address, session)
        except Exception as e:
            logger.error(f"Error adding team member: {e}", exc_info=True)
            return False
    
    async def _add_team_member(
        self,
        team_id: int,
        member_address: str,
        admin_address: str,
        session
    ) -> bool:
        """Add team member in database"""
        from database.models import Team, TeamMember
        from sqlalchemy import select
        
        try:
            # Verify admin
            result = await session.execute(
                select(Team).where(
                    Team.id == team_id,
                    Team.admin_address == admin_address
                )
            )
            team = result.scalar_one_or_none()
            
            if not team:
                return False
            
            # Check if member already exists
            member_result = await session.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.wallet_address == member_address
                )
            )
            existing = member_result.scalar_one_or_none()
            
            if existing:
                return False  # Already a member
            
            # Add member
            member = TeamMember(
                team_id=team_id,
                wallet_address=member_address,
                role='member'
            )
            session.add(member)
            await session.commit()
            
            logger.info(f"Added member {member_address} to team {team_id}")
            return True
        except Exception as e:
            logger.error(f"Error in _add_team_member: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def calculate_team_score(
        self,
        team_id: int,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate aggregate team credit score
        
        Args:
            team_id: Team ID
            session: Database session (optional)
            
        Returns:
            Team score dict
        """
        try:
            from database.connection import get_session
            from database.models import Team, TeamMember, Score
            from sqlalchemy import select, func
            
            if session is None:
                async with get_session() as db_session:
                    return await self._calculate_team_score(team_id, db_session)
            else:
                return await self._calculate_team_score(team_id, session)
        except Exception as e:
            logger.error(f"Error calculating team score: {e}", exc_info=True)
            return None
    
    async def _calculate_team_score(
        self,
        team_id: int,
        session
    ) -> Optional[Dict[str, Any]]:
        """Calculate team score from database"""
        from database.models import Team, TeamMember, Score, TeamScore
        from sqlalchemy import select, func
        
        try:
            # Get team
            result = await session.execute(
                select(Team).where(Team.id == team_id)
            )
            team = result.scalar_one_or_none()
            
            if not team:
                return None
            
            # Get all members
            members_result = await session.execute(
                select(TeamMember).where(TeamMember.team_id == team_id)
            )
            members = members_result.scalars().all()
            
            if len(members) < self.MIN_TEAM_MEMBERS:
                return {
                    "team_id": team_id,
                    "aggregate_score": 0,
                    "member_count": len(members),
                    "error": f"Team must have at least {self.MIN_TEAM_MEMBERS} members",
                }
            
            # Get scores for all members
            member_addresses = [m.wallet_address for m in members]
            scores_result = await session.execute(
                select(Score).where(Score.wallet_address.in_(member_addresses))
            )
            scores = scores_result.scalars().all()
            
            if not scores:
                return {
                    "team_id": team_id,
                    "aggregate_score": 0,
                    "member_count": len(members),
                    "error": "No scores found for team members",
                }
            
            # Calculate weighted average (by contribution score if available)
            total_weighted_score = Decimal('0')
            total_weight = Decimal('0')
            
            for member in members:
                # Find score for this member
                member_score = next((s for s in scores if s.wallet_address == member.wallet_address), None)
                if not member_score:
                    continue
                
                # Weight by contribution score (default 1.0)
                weight = Decimal(str(member.contribution_score)) if member.contribution_score else Decimal('1.0')
                
                total_weighted_score += Decimal(str(member_score.score)) * weight
                total_weight += weight
            
            if total_weight == 0:
                aggregate_score = 0
            else:
                aggregate_score = int(float(total_weighted_score / total_weight))
            
            # Save team score
            team_score = TeamScore(
                team_id=team_id,
                aggregate_score=aggregate_score,
                member_count=len(members)
            )
            session.add(team_score)
            await session.commit()
            
            return {
                "team_id": team_id,
                "team_name": team.team_name,
                "aggregate_score": aggregate_score,
                "member_count": len(members),
                "calculated_at": team_score.calculated_at.isoformat() if team_score.calculated_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _calculate_team_score: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def get_team_leaderboard(
        self,
        limit: int = 100,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get team leaderboard
        
        Args:
            limit: Number of teams to return
            session: Database session (optional)
            
        Returns:
            List of team score dicts
        """
        try:
            from database.connection import get_session
            from database.models import TeamScore, Team
            from sqlalchemy import select, desc, func
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_team_leaderboard(limit, db_session)
            else:
                return await self._get_team_leaderboard(limit, session)
        except Exception as e:
            logger.error(f"Error getting team leaderboard: {e}", exc_info=True)
            return []
    
    async def _get_team_leaderboard(
        self,
        limit: int,
        session
    ) -> List[Dict[str, Any]]:
        """Get team leaderboard from database"""
        from database.models import TeamScore, Team
        from sqlalchemy import select, desc, func
        
        try:
            # Get latest score for each team
            subquery = select(
                TeamScore.team_id,
                func.max(TeamScore.calculated_at).label('max_calculated_at')
            ).group_by(TeamScore.team_id).subquery()
            
            query = select(TeamScore, Team).join(
                Team, TeamScore.team_id == Team.id
            ).join(
                subquery,
                (TeamScore.team_id == subquery.c.team_id) &
                (TeamScore.calculated_at == subquery.c.max_calculated_at)
            ).order_by(desc(TeamScore.aggregate_score)).limit(limit)
            
            result = await session.execute(query)
            rows = result.all()
            
            return [
                {
                    "team_id": team_score.team_id,
                    "team_name": team.team_name,
                    "team_type": team.team_type,
                    "aggregate_score": team_score.aggregate_score,
                    "member_count": team_score.member_count,
                    "calculated_at": team_score.calculated_at.isoformat() if team_score.calculated_at else None,
                }
                for team_score, team in rows
            ]
        except Exception as e:
            logger.error(f"Error in _get_team_leaderboard: {e}", exc_info=True)
            return []
    
    async def get_team_stats(
        self,
        team_id: int,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Get team statistics
        
        Args:
            team_id: Team ID
            session: Database session (optional)
            
        Returns:
            Team stats dict
        """
        try:
            from database.connection import get_session
            from database.models import Team, TeamMember, TeamScore
            from sqlalchemy import select, func, desc
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_team_stats(team_id, db_session)
            else:
                return await self._get_team_stats(team_id, session)
        except Exception as e:
            logger.error(f"Error getting team stats: {e}", exc_info=True)
            return None
    
    async def _get_team_stats(
        self,
        team_id: int,
        session
    ) -> Optional[Dict[str, Any]]:
        """Get team stats from database"""
        from database.models import Team, TeamMember, TeamScore
        from sqlalchemy import select, func, desc
        
        try:
            # Get team
            result = await session.execute(
                select(Team).where(Team.id == team_id)
            )
            team = result.scalar_one_or_none()
            
            if not team:
                return None
            
            # Get members
            members_result = await session.execute(
                select(TeamMember).where(TeamMember.team_id == team_id)
            )
            members = members_result.scalars().all()
            
            # Get latest score
            score_result = await session.execute(
                select(TeamScore).where(
                    TeamScore.team_id == team_id
                ).order_by(desc(TeamScore.calculated_at)).limit(1)
            )
            latest_score = score_result.scalar_one_or_none()
            
            return {
                "team_id": team_id,
                "team_name": team.team_name,
                "team_type": team.team_type,
                "admin_address": team.admin_address,
                "member_count": len(members),
                "members": [
                    {
                        "wallet_address": m.wallet_address,
                        "role": m.role,
                        "contribution_score": float(m.contribution_score) if m.contribution_score else None,
                    }
                    for m in members
                ],
                "latest_score": {
                    "aggregate_score": latest_score.aggregate_score if latest_score else None,
                    "calculated_at": latest_score.calculated_at.isoformat() if latest_score and latest_score.calculated_at else None,
                } if latest_score else None,
                "created_at": team.created_at.isoformat() if team.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _get_team_stats: {e}", exc_info=True)
            return None

