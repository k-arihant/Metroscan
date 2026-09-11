import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

/// Backend API Configuration & Constants
/// Supports adaptive localhost detection and persistent runtime IP override
class ApiConstants {
  static String? _customHost;

  static String? get customHost => _customHost;

  static Future<void> loadCustomHost() async {
    if (kIsWeb) return;
    try {
      final docDir = await getApplicationDocumentsDirectory();
      final file = File('${docDir.path}/custom_host.txt');
      if (await file.exists()) {
        final saved = await file.readAsString();
        if (saved.trim().isNotEmpty) {
          _customHost = saved.trim().replaceAll(RegExp(r'/+$'), '');
          debugPrint('[ApiConstants] Loaded persistent custom host: $_customHost');
        }
      }
    } catch (e) {
      debugPrint('[ApiConstants] Error loading custom host: $e');
    }
  }

  static Future<void> setCustomHost(String host) async {
    _customHost = host.trim().replaceAll(RegExp(r'/+$'), '');
    if (kIsWeb) return;
    try {
      final docDir = await getApplicationDocumentsDirectory();
      final file = File('${docDir.path}/custom_host.txt');
      await file.writeAsString(_customHost!);
      debugPrint('[ApiConstants] Persisted custom host: $_customHost');
    } catch (e) {
      debugPrint('[ApiConstants] Error persisting custom host: $e');
    }
  }

  static String get baseUrl {
    if (_customHost != null && _customHost!.isNotEmpty) {
      return _customHost!;
    }
    if (kIsWeb) {
      return 'http://localhost:8000';
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        // 127.0.0.1 connects via 'adb reverse tcp:8000 tcp:8000' on real Android phones & emulators
        return 'http://127.0.0.1:8000';
      case TargetPlatform.windows:
      case TargetPlatform.macOS:
      case TargetPlatform.linux:
      default:
        return 'http://localhost:8000';
    }
  }

  static const String apiPrefix = '/api/v1';

  // Auth endpoints
  static String get loginUrl => '$baseUrl$apiPrefix/auth/login';
  static String get demoLoginUrl => '$baseUrl$apiPrefix/auth/demo-login';
  static String get signupUrl => '$baseUrl$apiPrefix/auth/signup';
  static String get meUrl => '$baseUrl$apiPrefix/auth/me';

  // Scanning endpoints
  static String get scanAnalyzeUrl => '$baseUrl$apiPrefix/scan/analyze';
  static String scanDetailUrl(String scanId) => '$baseUrl$apiPrefix/scan/$scanId';
  static String scanCertificatePdfUrl(String scanId) =>
      '$baseUrl$apiPrefix/scan/$scanId/certificate.pdf';
  static String scanReportPdfUrl(String scanId) =>
      '$baseUrl$apiPrefix/scan/$scanId/report.pdf';

  // Dashboard endpoints
  static String get dashboardStatsUrl => '$baseUrl$apiPrefix/dashboard/stats';
  static String get dashboardRecentScansUrl => '$baseUrl$apiPrefix/dashboard/recent-scans';
  static String get dashboardHeatmapUrl => '$baseUrl$apiPrefix/dashboard/heatmap';
  static String get dashboardAnalyticsUrl => '$baseUrl$apiPrefix/dashboard/analytics';

  // Health check
  static String get healthUrl => '$baseUrl/health';
}
