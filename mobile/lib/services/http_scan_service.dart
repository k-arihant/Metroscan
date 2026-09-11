import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../core/constants/api_constants.dart';
import '../models/scan_response.dart';
import 'auth_service.dart';
import 'http_auth_service.dart';
import 'scan_service.dart';
import 'mock/mock_data.dart';

class HttpScanService implements ScanService {
  final AuthService? _authService;

  HttpScanService({AuthService? authService}) : _authService = authService;

  final Map<String, ScanResponse> _cache = {
    MockData.sampleAashirvaadScan.scanId: MockData.sampleAashirvaadScan,
    MockData.sampleParleGScan.scanId: MockData.sampleParleGScan,
  };

  @override
  Future<ScanResponse> analyzePackage({
    required List<String> imagePaths,
    List<String>? panelTypes,
    String? storeName,
    double? latitude,
    double? longitude,
    String category = 'general',
  }) async {
    final uri = Uri.parse(ApiConstants.scanAnalyzeUrl);
    final req = http.MultipartRequest('POST', uri);

    // 1. Bearer Authentication and User Context
    final user = await _authService?.getCurrentUser();
    final authSvc = _authService;
    final token = (authSvc is HttpAuthService) ? authSvc.token : null;

    if (token != null && token.isNotEmpty) {
      req.headers['Authorization'] = 'Bearer $token';
    }

    if (user != null) {
      req.fields['user_id'] = user.id;
      req.fields['user_role'] = user.role.isOfficial ? 'inspector' : 'consumer';
    }

    if (storeName != null && storeName.trim().isNotEmpty) {
      req.fields['store_name'] = storeName.trim();
    }
    if (latitude != null) {
      req.fields['latitude'] = latitude.toString();
    }
    if (longitude != null) {
      req.fields['longitude'] = longitude.toString();
    }
    req.fields['category'] = category;

    // 2. Canonical Panels Definition
    const defaultPanels = ['front', 'back', 'mrp_panel', 'side', 'side', 'other'];
    final effectivePanels = panelTypes ?? defaultPanels;

    // 3. Attach all 1-6 actual package panel images
    final activePanels = <String>[];
    int attachedCount = 0;

    for (int i = 0; i < imagePaths.length; i++) {
      final path = imagePaths[i];
      final panelName = (i < effectivePanels.length) ? effectivePanels[i] : 'other';

      if (!kIsWeb && File(path).existsSync()) {
        final rawExt = path.split('.').last.toLowerCase();
        final ext = (rawExt == 'jpeg' || rawExt == 'png' || rawExt == 'webp') ? rawExt : 'jpg';
        final fileName = 'panel_${i + 1}_$panelName.$ext';

        req.files.add(
          await http.MultipartFile.fromPath(
            'images',
            path,
            filename: fileName,
          ),
        );
        activePanels.add(panelName);
        attachedCount++;
      } else if (path.startsWith('http://') || path.startsWith('https://')) {
        try {
          final fetchRes = await http.get(Uri.parse(path)).timeout(const Duration(seconds: 10));
          if (fetchRes.statusCode == 200 && fetchRes.bodyBytes.isNotEmpty) {
            req.files.add(
              http.MultipartFile.fromBytes(
                'images',
                fetchRes.bodyBytes,
                filename: 'panel_${i + 1}_$panelName.jpg',
              ),
            );
            activePanels.add(panelName);
            attachedCount++;
          }
        } catch (fetchErr) {
          debugPrint('[HttpScanService] Could not fetch remote sample photo: $fetchErr');
        }
      }
    }

    if (attachedCount == 0) {
      throw Exception('No valid package images captured. Please capture at least one package panel.');
    }

    // Set panel_types aligned with attached images
    req.fields['panel_types'] = activePanels.join(',');

    try {
      final streamedRes = await req.send().timeout(const Duration(seconds: 90));
      final res = await http.Response.fromStream(streamedRes);

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        final scan = ScanResponse.fromJson(data);
        _cache[scan.scanId] = scan;
        return scan;
      } else {
        final errData = jsonDecode(res.body) as Map<String, dynamic>?;
        final msg = errData?['detail'] ?? 'Statutory analysis failed with HTTP ${res.statusCode}';
        throw Exception(msg);
      }
    } catch (e) {
      debugPrint('[HttpScanService] Analysis request failed: $e');
      rethrow;
    }
  }

  @override
  Future<ScanResponse> getScanDetails(String scanId) async {
    if (_cache.containsKey(scanId)) {
      return _cache[scanId]!;
    }

    final authSvc = _authService;
    final token = (authSvc is HttpAuthService) ? authSvc.token : null;
    final headers = <String, String>{};
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }

    try {
      final res = await http.get(
        Uri.parse(ApiConstants.scanDetailUrl(scanId)),
        headers: headers.isNotEmpty ? headers : null,
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        final scan = ScanResponse.fromJson(data);
        _cache[scan.scanId] = scan;
        return scan;
      }
    } catch (e) {
      debugPrint('[HttpScanService] Error fetching scan details: $e');
    }

    return MockData.sampleAashirvaadScan.copyWith(scanId: scanId);
  }

  @override
  Future<ScanResponse> updateDeclaration({
    required String scanId,
    required String ruleCode,
    required String newValue,
  }) async {
    final current = await getScanDetails(scanId);

    final updatedDeclarations = current.declarations.map((d) {
      if (d.ruleCode == ruleCode) {
        return d.copyWith(
          extractedValue: newValue,
          status: 'PASS',
          isPresent: true,
          violationReason: null,
          confidenceScore: 1.0,
        );
      }
      return d;
    }).toList();

    // Recompute score: 10 pts per PASS, 5 pts per WARNING
    final earned = updatedDeclarations.fold<int>(
      0,
      (acc, d) => acc + (d.isPass ? 10 : (d.isWarning ? 5 : 0)),
    );
    final newScore = ((earned / (updatedDeclarations.length * 10)) * 100)
        .clamp(0.0, 100.0)
        .toDouble();

    final hasFail = updatedDeclarations.any((d) => d.isFail);
    final hasWarning = updatedDeclarations.any((d) => d.isWarning);
    final newStatus = hasFail
        ? 'NON_COMPLIANT'
        : (hasWarning ? 'WARNING' : 'COMPLIANT');

    final updatedScan = current.copyWith(
      declarations: updatedDeclarations,
      complianceScore: double.parse(newScore.toStringAsFixed(1)),
      overallStatus: newStatus,
    );

    _cache[scanId] = updatedScan;
    return updatedScan;
  }
}
