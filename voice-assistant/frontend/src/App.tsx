import { DashboardProvider } from "./context/DashboardContext";
import { Header } from "./components/layout/Header";
import { DashboardGrid, FullWidth } from "./components/layout/DashboardGrid";
import { StatsRow } from "./components/stats/StatsRow";
import { ComponentHealth } from "./components/health/ComponentHealth";
import { LatencyBreakdown } from "./components/latency/LatencyBreakdown";
import { TryItPanel } from "./components/tryit/TryItPanel";
import { LanguageDistribution } from "./components/languages/LanguageDistribution";
import { ConversationLog } from "./components/conversations/ConversationLog";
import { DashboardDataLoader } from "./DashboardDataLoader";

export function App() {
  return (
    <DashboardProvider>
      <DashboardDataLoader>
        <Header />
        <DashboardGrid>
          <StatsRow />
          <ComponentHealth />
          <LatencyBreakdown />
          <TryItPanel />
          <LanguageDistribution />
          <FullWidth>
            <ConversationLog />
          </FullWidth>
        </DashboardGrid>
      </DashboardDataLoader>
    </DashboardProvider>
  );
}
