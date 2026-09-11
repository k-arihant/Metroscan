import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/constants/app_colors.dart';
import '../../models/scan_response.dart';
import '../../providers/auth_provider.dart';
import '../../providers/scan_provider.dart';
import '../../services/http_auth_service.dart';
import '../../services/share_service.dart';
import '../../widgets/gov_app_bar.dart';
import '../../widgets/verdict_badge.dart';
import '../../widgets/declaration_card.dart';
import '../../widgets/bottom_distribution_bar.dart';
import '../../services/mock/mock_data.dart';
import 'field_editor_dialog.dart';

class ScorecardScreen extends ConsumerWidget {
  final String scanId;

  const ScorecardScreen({
    super.key,
    required this.scanId,
  });

  void _handleDownload(BuildContext context, ScanResponse scan, {bool isConsumer = false, String? token}) async {
    final res = await ShareService.downloadPdf(
      scanId: scan.scanId,
      productName: scan.productName,
      isConsumer: isConsumer,
      token: token,
    );
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(res.message),
          backgroundColor: AppColors.primaryBlue,
          action: SnackBarAction(
            label: 'View',
            textColor: AppColors.saffronLight,
            onPressed: () => context.push('/pdf-preview/${scan.scanId}'),
          ),
        ),
      );
    }
  }

  void _handleWhatsApp(BuildContext context, ScanResponse scan, {bool isConsumer = false, String? token}) async {
    final res = await ShareService.shareViaWhatsApp(
      scanId: scan.scanId,
      productName: scan.productName,
      score: scan.complianceScore,
      overallStatus: scan.overallStatus,
      isConsumer: isConsumer,
      token: token,
    );
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(res.message),
          backgroundColor: const Color(0xFF25D366),
        ),
      );
    }
  }

  void _handleEmail(BuildContext context, ScanResponse scan, {bool isConsumer = false, String? token}) async {
    final emailController = TextEditingController(text: isConsumer ? 'consumer@grievance.gov.in' : 'officer@gov.in');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(isConsumer ? 'Share Consumer Advisory Report' : 'Dispatch Statutory Legal Notice'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              isConsumer
                  ? 'Enter recipient email address to send packaging compliance record:'
                  : 'Enter recipient email (retailer, manufacturer, or department officer):',
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: emailController,
              decoration: const InputDecoration(
                labelText: 'Recipient Email',
                prefixIcon: Icon(Icons.email_outlined),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.of(ctx).pop();
              final res = await ShareService.sendViaEmail(
                scanId: scan.scanId,
                recipientEmail: emailController.text.trim(),
                productName: scan.productName,
                isConsumer: isConsumer,
                token: token,
              );
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(res.message),
                    backgroundColor: AppColors.saffron,
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.primaryBlue),
            child: Text(isConsumer ? 'Send Report' : 'Send Notice'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scanState = ref.watch(scanStateProvider);
    final authState = ref.watch(authStateProvider);
    final isInspector = authState.isInspector;
    final token = (ref.watch(authServiceProvider) is HttpAuthService)
        ? (ref.watch(authServiceProvider) as HttpAuthService).token
        : null;

    final scan = scanState.currentScan ??
        (scanId.contains('7a91')
            ? MockData.sampleParleGScan
            : MockData.sampleAashirvaadScan.copyWith(scanId: scanId));

    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: GovAppBar(
        title: isInspector ? 'Statutory Compliance Scorecard' : 'Consumer Advisory Scorecard',
        subtitle: 'Form 1 Verification Dossier #${scan.scanId.length > 8 ? scan.scanId.substring(0, 8) : scan.scanId}',
        onBackPressed: () => context.go('/dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.picture_as_pdf_outlined, color: Colors.white),
            tooltip: isInspector ? 'View Official PDF Notice' : 'View Consumer Report',
            onPressed: () => context.push('/pdf-preview/${scan.scanId}'),
          ),
        ],
      ),
      bottomNavigationBar: BottomDistributionBar(
        onDownload: () => _handleDownload(context, scan, isConsumer: !isInspector, token: token),
        onWhatsApp: () => _handleWhatsApp(context, scan, isConsumer: !isInspector, token: token),
        onEmail: () => _handleEmail(context, scan, isConsumer: !isInspector, token: token),
        onPreviewPdf: () => context.push('/pdf-preview/${scan.scanId}'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Overall Verdict Header Card
            VerdictBadge(scan: scan),
            const SizedBox(height: 20),

            // Legal Metrology 10-Point Checklist Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '10-POINT STATUTORY DECLARATIONS',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: AppColors.textSecondary,
                    letterSpacing: 0.5,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.canvas,
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: AppColors.cardBorder),
                  ),
                  child: const Text(
                    '2011 RULES',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Declaration Cards List
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: scan.declarations.length,
              itemBuilder: (context, index) {
                final decl = scan.declarations[index];
                return DeclarationCard(
                  declaration: decl,
                  onEdit: () {
                    FieldEditorDialog.show(
                      context: context,
                      declaration: decl,
                      onSave: (val) {
                        ref.read(scanStateProvider.notifier).updateField(
                              ruleCode: decl.ruleCode,
                              newValue: val,
                            );
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Updated ${decl.ruleName} to "$val"'),
                            backgroundColor: AppColors.compliantGreen,
                          ),
                        );
                      },
                    );
                  },
                );
              },
            ),

            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
