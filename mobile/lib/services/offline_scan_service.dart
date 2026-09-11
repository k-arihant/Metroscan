import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import '../models/scan_response.dart';
import 'scan_service.dart';

class OfflineScanRecord {
  final String id;
  final DateTime createdAt;
  final String? storeName;
  final double? latitude;
  final double? longitude;
  final String category;
  final List<String> panelTypes;
  final List<String> localImagePaths;

  const OfflineScanRecord({
    required this.id,
    required this.createdAt,
    this.storeName,
    this.latitude,
    this.longitude,
    required this.category,
    required this.panelTypes,
    required this.localImagePaths,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'createdAt': createdAt.toIso8601String(),
        'storeName': storeName,
        'latitude': latitude,
        'longitude': longitude,
        'category': category,
        'panelTypes': panelTypes,
        'localImagePaths': localImagePaths,
      };

  factory OfflineScanRecord.fromJson(Map<String, dynamic> json) => OfflineScanRecord(
        id: json['id'] as String,
        createdAt: DateTime.tryParse(json['createdAt'] as String? ?? '') ?? DateTime.now(),
        storeName: json['storeName'] as String?,
        latitude: (json['latitude'] as num?)?.toDouble(),
        longitude: (json['longitude'] as num?)?.toDouble(),
        category: json['category'] as String? ?? 'food',
        panelTypes: (json['panelTypes'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
        localImagePaths: (json['localImagePaths'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      );
}

class OfflineScanService {
  static Future<Directory> _getOfflineDir() async {
    final docDir = await getApplicationDocumentsDirectory();
    final offlineDir = Directory('${docDir.path}/offline_scans');
    if (!await offlineDir.exists()) {
      await offlineDir.create(recursive: true);
    }
    return offlineDir;
  }

  /// Saves a pending inspection when network is unreachable or device is in offline mode
  static Future<OfflineScanRecord> savePendingScan({
    required List<String> imagePaths,
    List<String>? panelTypes,
    String? storeName,
    double? latitude,
    double? longitude,
    String category = 'food',
  }) async {
    final offlineDir = await _getOfflineDir();
    final scanId = 'offline_${DateTime.now().millisecondsSinceEpoch}';
    final targetScanDir = Directory('${offlineDir.path}/$scanId');
    await targetScanDir.create(recursive: true);

    final savedImagePaths = <String>[];
    for (int i = 0; i < imagePaths.length; i++) {
      final srcPath = imagePaths[i];
      final srcFile = File(srcPath);
      if (await srcFile.exists()) {
        final ext = srcPath.split('.').last.toLowerCase();
        final destPath = '${targetScanDir.path}/panel_${i + 1}.$ext';
        await srcFile.copy(destPath);
        savedImagePaths.add(destPath);
      }
    }

    final record = OfflineScanRecord(
      id: scanId,
      createdAt: DateTime.now(),
      storeName: storeName ?? 'Field Mandi / Retail Outlet',
      latitude: latitude,
      longitude: longitude,
      category: category,
      panelTypes: panelTypes ?? const ['front', 'back', 'mrp_panel', 'side', 'side', 'other'],
      localImagePaths: savedImagePaths,
    );

    final metaFile = File('${targetScanDir.path}/meta.json');
    await metaFile.writeAsString(jsonEncode(record.toJson()));

    debugPrint('[OfflineScanService] Saved pending offline scan: $scanId with ${savedImagePaths.length} images');
    return record;
  }

  /// Returns all pending offline scans awaiting synchronization
  static Future<List<OfflineScanRecord>> getPendingScans() async {
    if (kIsWeb) return [];
    try {
      final offlineDir = await _getOfflineDir();
      final entities = await offlineDir.list().toList();
      final records = <OfflineScanRecord>[];

      for (final entity in entities) {
        if (entity is Directory) {
          final metaFile = File('${entity.path}/meta.json');
          if (await metaFile.exists()) {
            try {
              final content = await metaFile.readAsString();
              final json = jsonDecode(content) as Map<String, dynamic>;
              records.add(OfflineScanRecord.fromJson(json));
            } catch (e) {
              debugPrint('[OfflineScanService] Error reading scan meta: $e');
            }
          }
        }
      }

      records.sort((a, b) => b.createdAt.compareTo(a.createdAt));
      return records;
    } catch (e) {
      debugPrint('[OfflineScanService] Error listing pending scans: $e');
      return [];
    }
  }

  /// Returns count of pending offline audits
  static Future<int> getPendingCount() async {
    final scans = await getPendingScans();
    return scans.length;
  }

  /// Removes a pending scan after successful synchronization
  static Future<void> deletePendingScan(String id) async {
    try {
      final offlineDir = await _getOfflineDir();
      final scanDir = Directory('${offlineDir.path}/$id');
      if (await scanDir.exists()) {
        await scanDir.delete(recursive: true);
        debugPrint('[OfflineScanService] Deleted synchronized offline scan: $id');
      }
    } catch (e) {
      debugPrint('[OfflineScanService] Error deleting offline scan: $e');
    }
  }

  /// Syncs all pending offline audits to canonical backend
  static Future<List<ScanResponse>> syncAll(ScanService scanService) async {
    final pending = await getPendingScans();
    final syncedScans = <ScanResponse>[];

    for (final record in pending) {
      try {
        final res = await scanService.analyzePackage(
          imagePaths: record.localImagePaths,
          panelTypes: record.panelTypes,
          storeName: record.storeName,
          latitude: record.latitude,
          longitude: record.longitude,
          category: record.category,
        );

        syncedScans.add(res);
        await deletePendingScan(record.id);
        debugPrint('[OfflineScanService] Successfully synced and cleared: ${record.id}');
      } catch (e) {
        debugPrint('[OfflineScanService] Failed to sync ${record.id}: $e');
      }
    }

    return syncedScans;
  }
}
