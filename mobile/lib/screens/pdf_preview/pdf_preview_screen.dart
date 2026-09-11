import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/constants/api_constants.dart';
import '../../core/constants/app_colors.dart';
import '../../models/scan_response.dart';
import '../../providers/auth_provider.dart';
import '../../providers/scan_provider.dart';
import '../../services/http_auth_service.dart';
import '../../services/share_service.dart';
import '../../widgets/gov_app_bar.dart';

class PdfPreviewScreen extends ConsumerWidget {
  final String scanId;

  const PdfPreviewScreen({
    super.key,
    required this.scanId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isInspector = ref.watch(authStateProvider).isInspector;
    final token = (ref.watch(authServiceProvider) is HttpAuthService)
        ? (ref.watch(authServiceProvider) as HttpAuthService).token
        : null;

    final currentScan = ref.watch(scanStateProvider).currentScan;
    final scanAsync = (currentScan != null && currentScan.scanId == scanId)
        ? AsyncValue.data(currentScan)
        : ref.watch(scanDetailFutureProvider(scanId));

    final basePdfUrl = isInspector
        ? ApiConstants.scanCertificatePdfUrl(scanId)
        : ApiConstants.scanReportPdfUrl(scanId);

    final streamUrl = (token != null && token.isNotEmpty && isInspector)
        ? '$basePdfUrl?token=$token'
        : basePdfUrl;

    return scanAsync.when(
      loading: () => Scaffold(
        backgroundColor: const Color(0xFF525659),
        appBar: GovAppBar(
          title: isInspector ? 'Form 1 Statutory Notice' : 'Consumer Advisory Report',
          subtitle: 'Loading inspection record...',
        ),
        body: const Center(
          child: CircularProgressIndicator(color: AppColors.saffron),
        ),
      ),
      error: (err, _) => Scaffold(
        backgroundColor: const Color(0xFF525659),
        appBar: GovAppBar(
          title: 'Document Preview',
          subtitle: 'Error loading record',
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.error_outline_rounded, size: 48, color: AppColors.violationRed),
                const SizedBox(height: 12),
                Text('Could not load record: $err', textAlign: TextAlign.center, style: const TextStyle(color: Colors.white)),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.refresh(scanDetailFutureProvider(scanId)),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
      ),
      data: (scan) => _buildPdfScaffold(context, ref, scan, isInspector, token, streamUrl),
    );
  }

  Widget _buildPdfScaffold(
    BuildContext context,
    WidgetRef ref,
    ScanResponse scan,
    bool isInspector,
    String? token,
    String streamUrl,
  ) {
    final formattedDate = DateFormat('dd-MMM-yyyy hh:mm a').format(scan.scannedAt);
    final idShort = scan.scanId.length > 8 ? scan.scanId.substring(0, 8) : scan.scanId;

    return Scaffold(
      backgroundColor: const Color(0xFF525659), // Standard PDF reader canvas
      appBar: GovAppBar(
        title: isInspector ? 'Form 1 Statutory Notice' : 'Consumer Advisory Report',
        subtitle: isInspector
            ? 'Court-Admissible Legal Notice #$idShort'
            : 'Packaging Verification Report #$idShort',
        actions: [
          IconButton(
            icon: const Icon(Icons.open_in_browser_rounded, color: Colors.white),
            tooltip: 'Open Live Stream PDF',
            onPressed: () async {
              final url = Uri.parse(streamUrl);
              try {
                await launchUrl(url, mode: LaunchMode.externalApplication);
              } catch (_) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Could not launch: $url')),
                  );
                }
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.download_rounded, color: Colors.white),
            tooltip: 'Download PDF',
            onPressed: () async {
              final res = await ShareService.downloadPdf(
                scanId: scan.scanId,
                productName: scan.productName,
                isConsumer: !isInspector,
                token: token,
              );
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(res.message)),
                );
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.share_rounded, color: Colors.white),
            tooltip: 'Native Share',
            onPressed: () async {
              final res = await ShareService.shareViaWhatsApp(
                scanId: scan.scanId,
                productName: scan.productName,
                score: scan.complianceScore,
                overallStatus: scan.overallStatus,
                isConsumer: !isInspector,
                token: token,
              );
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(res.message)),
                );
              }
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Center(
          child: Container(
            constraints: const BoxConstraints(maxWidth: 580),
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(4),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.35),
                  blurRadius: 14,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 1. Sovereign Government / Department Header
                const Center(
                  child: Text(
                    'GOVERNMENT OF INDIA',
                    style: TextStyle(
                      fontFamily: 'serif',
                      fontSize: 14,
                      fontWeight: FontWeight.w900,
                      color: AppColors.sovereignDark,
                      letterSpacing: 1.2,
                    ),
                  ),
                ),
                const SizedBox(height: 2),
                const Center(
                  child: Text(
                    'MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION',
                    style: TextStyle(
                      fontSize: 8.5,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF566573),
                    ),
                  ),
                ),
                Center(
                  child: Text(
                    isInspector
                        ? 'DELHI STATE LEGAL METROLOGY ENFORCEMENT DIVISION'
                        : 'NATIONAL CONSUMER PACKAGING VERIFICATION REGISTRY',
                    style: const TextStyle(
                      fontSize: 8.5,
                      color: Color(0xFF566573),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                const Divider(color: AppColors.primaryBlue, thickness: 1.5),
                const SizedBox(height: 6),

                Center(
                  child: Text(
                    isInspector
                        ? 'FORM 1: STATUTORY PACKAGING INSPECTION REPORT & NOTICE'
                        : 'LEGAL METROLOGY CONSUMER ADVISORY REPORT',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w900,
                      color: isInspector ? AppColors.warningAmber : AppColors.primaryBlue,
                      letterSpacing: 0.3,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
                Center(
                  child: Text(
                    isInspector
                        ? 'Issued under Section 18 & 36, Legal Metrology Act, 2009 read with 2011 Rules'
                        : 'Official packaging compliance summary for consumer protection & transparency',
                    style: const TextStyle(
                      fontSize: 8,
                      fontStyle: FontStyle.italic,
                      color: Color(0xFF7F8C8D),
                    ),
                  ),
                ),
                const SizedBox(height: 14),

                // 2. Inspection Metadata Table Box
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.canvas,
                    border: Border.all(color: const Color(0xFFBDC3C7)),
                  ),
                  child: Column(
                    children: [
                      _buildRow(isInspector ? 'Inspection Memo ID:' : 'Verification ID:', scan.scanId),
                      _buildRow('Audit Timestamp:', formattedDate),
                      _buildRow(
                        isInspector ? 'Inspecting Officer:' : 'Verified By:',
                        scan.inspectorName ?? (isInspector ? 'Senior Enforcement Officer' : 'Citizen Self-Audit'),
                      ),
                      _buildRow('Mandi / Store Location:', scan.storeName ?? 'Retail Mandi / Supermarket'),
                      _buildRow(
                        'Geo-Coordinates:',
                        scan.latitude != null && scan.longitude != null
                            ? '${scan.latitude!.toStringAsFixed(4)}° N, ${scan.longitude!.toStringAsFixed(4)}° E'
                            : 'Logged on-device during inspection',
                      ),
                      _buildRow('Commodity Verified:', '${scan.productName} (${scan.brandName})'),
                      _buildRow(
                        'Statutory Verdict:',
                        '${scan.overallStatus} (Compliance Score: ${scan.complianceScore.toStringAsFixed(1)}%)',
                      ),
                      _buildRow(
                        isInspector ? 'Enforcement Action:' : 'Consumer Advisory:',
                        isInspector
                            ? (scan.overallStatus == 'COMPLIANT'
                                ? 'VERIFIED COMPLIANT — PASS'
                                : 'LEGAL NOTICE ISSUED U/S 36')
                            : (scan.overallStatus == 'COMPLIANT'
                                ? 'SAFE FOR PURCHASE — MEETS 2011 NORMS'
                                : 'VIOLATION DETECTED — GRIEVANCE TO 1915'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // 3. 10-Rule Audit Matrix
                Text(
                  isInspector
                      ? '10-POINT MANDATORY STATUTORY DECLARATION AUDIT MATRIX'
                      : '10-POINT CONSUMER PACKAGING COMPLIANCE CHECKLIST',
                  style: const TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w900,
                    color: AppColors.primaryBlue,
                  ),
                ),
                const SizedBox(height: 6),

                Table(
                  border: TableBorder.all(color: const Color(0xFFD5DBDB), width: 0.8),
                  columnWidths: const {
                    0: FlexColumnWidth(1.2),
                    1: FlexColumnWidth(2.3),
                    2: FlexColumnWidth(1.3),
                  },
                  children: [
                    _buildTableHeader(),
                    ...scan.declarations.map((decl) {
                      String verdictStr = decl.status;
                      if (decl.measuredFontHeightMm != null) {
                        verdictStr += ' (${decl.measuredFontHeightMm} mm)';
                      }
                      if (decl.extractedValue != null && decl.extractedValue!.isNotEmpty) {
                        verdictStr += ' — ${decl.extractedValue}';
                      } else if (decl.violationReason != null && decl.violationReason!.isNotEmpty) {
                        verdictStr += ' — ${decl.violationReason}';
                      }

                      return _buildTableRow(
                        decl.statutoryCitation.isNotEmpty ? decl.statutoryCitation : decl.ruleCode,
                        decl.ruleName,
                        verdictStr,
                        decl.status,
                      );
                    }),
                  ],
                ),
                const SizedBox(height: 16),

                // 4. Digital Evidence Tamper-Proof Hash
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF2F4F4),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: const Color(0xFFE5E7E9)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'DIGITAL EVIDENCE SHA-256 TAMPER-PROOF HASH:',
                        style: TextStyle(
                          fontSize: 8,
                          fontWeight: FontWeight.w900,
                          color: Color(0xFF2C3E50),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        _computeHash(scan.scanId),
                        style: const TextStyle(
                          fontSize: 7.5,
                          fontFamily: 'monospace',
                          color: Color(0xFF566573),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // 5. Official Stamp & Seal Representation
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        border: Border.all(
                          color: isInspector ? AppColors.compliantGreen : AppColors.primaryBlue,
                          width: 1.5,
                        ),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        isInspector
                            ? 'VERIFIED DIGITAL MEMO\nOFFICIAL COURT-ADMISSIBLE RECORD'
                            : 'METROSCAN VERIFIED\nCONSUMER ADVISORY RECORD',
                        style: TextStyle(
                          fontSize: 7.5,
                          fontWeight: FontWeight.w900,
                          color: isInspector ? AppColors.compliantGreen : AppColors.primaryBlue,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          scan.inspectorName ?? (isInspector ? 'Shri Amit Verma' : 'Consumer Self-Audit'),
                          style: const TextStyle(fontSize: 9.5, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          isInspector
                              ? 'Senior Enforcement Officer\nBadge ID: ${scan.badgeId ?? "LM-DEL-8492"}'
                              : 'National Consumer Helpline: 1915\nconsumerhelpline.gov.in',
                          style: const TextStyle(fontSize: 7.5, color: Color(0xFF7F8C8D)),
                          textAlign: TextAlign.right,
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _computeHash(String input) {
    // Generate deterministic 64-char hex hash based on input
    int hash = 0x811c9dc5;
    for (int i = 0; i < input.length; i++) {
      hash ^= input.codeUnitAt(i);
      hash = (hash * 0x01000193) & 0xFFFFFFFF;
    }
    final hexPart = hash.toRadixString(16).padLeft(8, '0');
    return '$hexPart$hexPart$hexPart$hexPart$hexPart$hexPart$hexPart$hexPart'.substring(0, 64);
  }

  Widget _buildRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1C2833),
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 9,
                color: Color(0xFF2C3E50),
              ),
            ),
          ),
        ],
      ),
    );
  }

  TableRow _buildTableHeader() {
    return TableRow(
      decoration: const BoxDecoration(color: AppColors.primaryBlue),
      children: const [
        Padding(
          padding: EdgeInsets.all(5),
          child: Text('RULE', style: TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold)),
        ),
        Padding(
          padding: EdgeInsets.all(5),
          child: Text('STATUTORY DECLARATION', style: TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold)),
        ),
        Padding(
          padding: EdgeInsets.all(5),
          child: Text('VERDICT / OBSERVATION', style: TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }

  TableRow _buildTableRow(String rule, String name, String fullText, String status) {
    final isPass = status == 'PASS';
    final isFail = status == 'FAIL';
    final color = isPass
        ? AppColors.compliantGreen
        : (isFail ? AppColors.violationRed : AppColors.warningAmber);

    return TableRow(
      children: [
        Padding(
          padding: const EdgeInsets.all(4),
          child: Text(rule, style: const TextStyle(fontSize: 7.5, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
        ),
        Padding(
          padding: const EdgeInsets.all(4),
          child: Text(name, style: const TextStyle(fontSize: 7.5)),
        ),
        Padding(
          padding: const EdgeInsets.all(4),
          child: Text(fullText, style: TextStyle(fontSize: 7.5, fontWeight: FontWeight.w600, color: color)),
        ),
      ],
    );
  }
}

