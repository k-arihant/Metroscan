import 'declaration_result.dart';

class ScanResponse {
  final String scanId;
  final String productName;
  final String brandName;
  final String overallStatus; // "COMPLIANT" | "NON_COMPLIANT" | "WARNING"
  final double complianceScore;
  final List<DeclarationResult> declarations;
  final List<String> imageUrls;
  final List<String> annotatedImageUrls;
  final String? pdfUrl;
  final DateTime createdAt;
  final String? storeName;
  final double? latitude;
  final double? longitude;
  final String? inspectorName;
  final String? badgeId;

  const ScanResponse({
    required this.scanId,
    required this.productName,
    required this.brandName,
    required this.overallStatus,
    required this.complianceScore,
    required this.declarations,
    required this.imageUrls,
    required this.annotatedImageUrls,
    this.pdfUrl,
    required this.createdAt,
    this.storeName,
    this.latitude,
    this.longitude,
    this.inspectorName,
    this.badgeId,
  });

  DateTime get scannedAt => createdAt;

  bool get isCompliant => overallStatus.toUpperCase() == 'COMPLIANT';
  bool get isNonCompliant => overallStatus.toUpperCase() == 'NON_COMPLIANT';
  bool get isWarning => overallStatus.toUpperCase() == 'WARNING';

  int get passCount => declarations.where((d) => d.isPass).length;
  int get failCount => declarations.where((d) => d.isFail).length;
  int get warningCount => declarations.where((d) => d.isWarning).length;

  factory ScanResponse.fromJson(Map<String, dynamic> json) {
    return ScanResponse(
      scanId: json['scan_id'] as String? ?? '',
      productName: json['product_name'] as String? ?? 'Packaged Commodity',
      brandName: json['brand_name'] as String? ?? 'Brand',
      overallStatus: json['overall_status'] as String? ?? 'WARNING',
      complianceScore: json['compliance_score'] != null
          ? (json['compliance_score'] as num).toDouble()
          : 0.0,
      declarations: (json['declarations'] as List<dynamic>?)
              ?.map((e) => DeclarationResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      imageUrls: (json['image_urls'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      annotatedImageUrls: (json['annotated_image_urls'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      pdfUrl: json['pdf_url'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      storeName: json['store_name'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      inspectorName: json['inspector_name'] as String?,
      badgeId: json['badge_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'scan_id': scanId,
    'product_name': productName,
    'brand_name': brandName,
    'overall_status': overallStatus,
    'compliance_score': complianceScore,
    'declarations': declarations.map((d) => d.toJson()).toList(),
    'image_urls': imageUrls,
    'annotated_image_urls': annotatedImageUrls,
    'pdf_url': pdfUrl,
    'created_at': createdAt.toIso8601String(),
    'store_name': storeName,
    'latitude': latitude,
    'longitude': longitude,
    'inspector_name': inspectorName,
    'badge_id': badgeId,
  };

  ScanResponse copyWith({
    String? scanId,
    String? productName,
    String? brandName,
    String? overallStatus,
    double? complianceScore,
    List<DeclarationResult>? declarations,
    List<String>? imageUrls,
    List<String>? annotatedImageUrls,
    String? pdfUrl,
    DateTime? createdAt,
    String? storeName,
    double? latitude,
    double? longitude,
    String? inspectorName,
    String? badgeId,
  }) {
    return ScanResponse(
      scanId: scanId ?? this.scanId,
      productName: productName ?? this.productName,
      brandName: brandName ?? this.brandName,
      overallStatus: overallStatus ?? this.overallStatus,
      complianceScore: complianceScore ?? this.complianceScore,
      declarations: declarations ?? this.declarations,
      imageUrls: imageUrls ?? this.imageUrls,
      annotatedImageUrls: annotatedImageUrls ?? this.annotatedImageUrls,
      pdfUrl: pdfUrl ?? this.pdfUrl,
      createdAt: createdAt ?? this.createdAt,
      storeName: storeName ?? this.storeName,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      inspectorName: inspectorName ?? this.inspectorName,
      badgeId: badgeId ?? this.badgeId,
    );
  }
}
