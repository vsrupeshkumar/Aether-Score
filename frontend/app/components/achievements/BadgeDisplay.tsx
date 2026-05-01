"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { getApiUrl } from "@/lib/api";
import { LoadingSpinner } from "@/app/components/ui/LoadingSpinner";
import { Badge } from "@/app/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs";

interface BadgeDisplayProps {
  address: string;
}

export function BadgeDisplay({ address }: BadgeDisplayProps) {
  const [badges, setBadges] = useState<any[]>([]);
  const [allAchievements, setAllAchievements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBadges = async () => {
      try {
        const [badgesRes, achievementsRes] = await Promise.all([
          fetch(`${getApiUrl()}/api/achievements/badges/${address}`),
          fetch(`${getApiUrl()}/api/achievements/list`),
        ]);

        if (badgesRes.ok) {
          const badgesData = await badgesRes.json();
          setBadges(badgesData.badges || []);
        }

        if (achievementsRes.ok) {
          const achievementsData = await achievementsRes.json();
          setAllAchievements(achievementsData.achievements || []);
        }
      } catch (error) {
        console.error("Error fetching badges:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchBadges();
  }, [address]);

  if (loading) {
    return <LoadingSpinner />;
  }

  const unlockedIds = new Set(badges.map((b) => b.achievement_id));
  const unlocked = allAchievements.filter((a) => unlockedIds.has(a.achievement_id));
  const locked = allAchievements.filter((a) => !unlockedIds.has(a.achievement_id));

  const groupedByCategory = (achievements: any[]) => {
    const grouped: Record<string, any[]> = {};
    achievements.forEach((a) => {
      const category = a.category || "general";
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(a);
    });
    return grouped;
  };

  const unlockedGrouped = groupedByCategory(unlocked);
  const lockedGrouped = groupedByCategory(locked);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Achievement Badges</CardTitle>
        <CardDescription>Your unlocked achievements and milestones</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="unlocked" className="space-y-4">
          <TabsList>
            <TabsTrigger value="unlocked">
              Unlocked ({unlocked.length})
            </TabsTrigger>
            <TabsTrigger value="all">
              All ({allAchievements.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="unlocked" className="space-y-6">
            {Object.keys(unlockedGrouped).length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No badges unlocked yet. Keep using AETHER-SCORE to unlock achievements!
              </div>
            ) : (
              Object.entries(unlockedGrouped).map(([category, achievements]) => (
                <div key={category}>
                  <h3 className="text-lg font-semibold mb-3 capitalize">{category} Badges</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {achievements.map((achievement) => {
                      const badge = badges.find((b) => b.achievement_id === achievement.achievement_id);
                      return (
                        <div
                          key={achievement.achievement_id}
                          className="p-4 border rounded-lg bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200"
                        >
                          <div className="text-4xl mb-2">{achievement.icon || "ðŸ…"}</div>
                          <div className="font-semibold text-sm">{achievement.name}</div>
                          <div className="text-xs text-gray-600 mt-1">{achievement.description}</div>
                          {badge?.unlocked_at && (
                            <div className="text-xs text-gray-500 mt-2">
                              Unlocked: {new Date(badge.unlocked_at).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </TabsContent>

          <TabsContent value="all" className="space-y-6">
            {Object.entries({ ...unlockedGrouped, ...lockedGrouped }).map(([category, achievements]) => (
              <div key={category}>
                <h3 className="text-lg font-semibold mb-3 capitalize">{category} Badges</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {achievements.map((achievement) => {
                    const isUnlocked = unlockedIds.has(achievement.achievement_id);
                    const badge = badges.find((b) => b.achievement_id === achievement.achievement_id);
                    return (
                      <div
                        key={achievement.achievement_id}
                        className={`p-4 border rounded-lg ${
                          isUnlocked
                            ? "bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200"
                            : "bg-gray-50 border-gray-200 opacity-60"
                        }`}
                      >
                        <div className="text-4xl mb-2 filter grayscale={isUnlocked ? 0 : 1}">
                          {achievement.icon || "ðŸ…"}
                        </div>
                        <div className="font-semibold text-sm">{achievement.name}</div>
                        <div className="text-xs text-gray-600 mt-1">{achievement.description}</div>
                        {isUnlocked && badge?.unlocked_at && (
                          <div className="text-xs text-gray-500 mt-2">
                            Unlocked: {new Date(badge.unlocked_at).toLocaleDateString()}
                          </div>
                        )}
                        {!isUnlocked && (
                          <Badge variant="outline" className="mt-2 text-xs">
                            Locked
                          </Badge>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}


