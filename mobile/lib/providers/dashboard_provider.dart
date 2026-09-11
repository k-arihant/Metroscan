import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/dashboard_stats.dart';
import '../models/recent_scan.dart';
import '../services/dashboard_service.dart';
import '../services/http_dashboard_service.dart';

import 'auth_provider.dart';

final dashboardServiceProvider = Provider<DashboardService>((ref) {
  final authService = ref.watch(authServiceProvider);
  return HttpDashboardService(authService: authService);
});

final dashboardStatsProvider = FutureProvider<DashboardStats>((ref) async {
  final service = ref.watch(dashboardServiceProvider);
  return service.getStats();
});

final scanFilterQueryProvider = StateProvider<String>((ref) => '');
final scanFilterStatusProvider = StateProvider<String>((ref) => 'ALL');

final recentScansProvider = FutureProvider<List<RecentScan>>((ref) async {
  final service = ref.watch(dashboardServiceProvider);
  final query = ref.watch(scanFilterQueryProvider);
  final status = ref.watch(scanFilterStatusProvider);
  return service.getRecentScans(query: query, status: status);
});
