import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/scan_provider.dart';
import '../../services/offline_scan_service.dart';

class ProcessingScreen extends ConsumerStatefulWidget {
  const ProcessingScreen({super.key});

  @override
  ConsumerState<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends ConsumerState<ProcessingScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _startAnalysis();
    });
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  Future<void> _startAnalysis() async {
    final images = ref.read(capturedImagesProvider);
    final panelTypes = ref.read(capturedPanelTypesProvider);
    final category = ref.read(selectedCategoryProvider);
    final storeName = ref.read(currentStoreNameProvider);

    final result = await ref.read(scanStateProvider.notifier).runAnalysis(
      images: images,
      panelTypes: panelTypes.isNotEmpty ? panelTypes : null,
      category: category,
      storeName: storeName,
    );

    if (!mounted) return;

    if (result != null) {
      context.go('/scorecard/${result.scanId}');
    } else {
      final err = ref.read(scanStateProvider).error ?? 'Processing failed. Please retake photo.';
      final isNetworkError = err.toLowerCase().contains('socket') ||
          err.toLowerCase().contains('connection') ||
          err.toLowerCase().contains('timeout') ||
          err.toLowerCase().contains('network') ||
          err.toLowerCase().contains('unreachable') ||
          err.toLowerCase().contains('failed host lookup') ||
          err.toLowerCase().contains('clientexception');

      if (isNetworkError) {
        final messenger = ScaffoldMessenger.of(context);
        final router = GoRouter.of(context);
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (ctx) => AlertDialog(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            title: const Row(
              children: [
                Icon(Icons.cloud_off_rounded, color: AppColors.saffron),
                SizedBox(width: 8),
                Expanded(
                  child: Text('Save Inspection Offline?', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            content: const Text(
              'Backend server is unreachable. Would you like to save this evidence package locally in your offline audit queue to sync when connected?',
              style: TextStyle(fontSize: 13),
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.of(ctx).pop();
                  if (mounted) {
                    if (router.canPop()) {
                      router.pop();
                    } else {
                      router.go('/dashboard');
                    }
                  }
                },
                child: const Text('Discard'),
              ),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.primaryBlue),
                icon: const Icon(Icons.save_rounded, size: 16, color: Colors.white),
                label: const Text('Save Offline', style: TextStyle(color: Colors.white)),
                onPressed: () async {
                  Navigator.of(ctx).pop();
                  await OfflineScanService.savePendingScan(
                    imagePaths: images,
                    panelTypes: panelTypes.isNotEmpty ? panelTypes : null,
                    category: category,
                    storeName: storeName,
                  );
                  if (mounted) {
                    messenger.showSnackBar(
                      const SnackBar(
                        content: Text('Saved to offline audit queue. Sync anytime from Dashboard!'),
                        backgroundColor: AppColors.compliantGreen,
                        duration: Duration(seconds: 4),
                      ),
                    );
                    router.go('/dashboard');
                  }
                },
              ),
            ],
          ),
        );
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(err),
          backgroundColor: AppColors.violationRed,
          duration: const Duration(seconds: 4),
        ),
      );
      if (context.canPop()) {
        context.pop();
      } else {
        context.go('/dashboard');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final scanState = ref.watch(scanStateProvider);
    final currentStep = scanState.analysisStep;

    return Scaffold(
      backgroundColor: AppColors.sovereignDark,
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Spacer(),
                // Animated Scanning Radar Target
                RotationTransition(
                  turns: _animController,
                  child: Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.saffronLight, width: 2),
                      gradient: SweepGradient(
                        colors: [
                          AppColors.saffronLight.withOpacity(0.0),
                          AppColors.saffronLight.withOpacity(0.3),
                        ],
                      ),
                    ),
                    child: Center(
                      child: Container(
                        width: 50,
                        height: 50,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: AppColors.primaryBlue,
                        ),
                        child: const Icon(Icons.document_scanner_rounded,
                            color: Colors.white, size: 26),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 28),

                const Text(
                  'STATUTORY COMPLIANCE AUDIT',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                    letterSpacing: 0.8,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Evaluating under Packaged Commodities Rules, 2011',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.white.withOpacity(0.7),
                  ),
                ),
                const SizedBox(height: 32),

                // Multi-Stage Pipeline Progress List
                _buildStepRow(
                  stepNum: 1,
                  title: 'Optimizing & Deskewing Images',
                  subtitle: 'Normalized contrast and orientation',
                  isActive: currentStep == 1,
                  isDone: currentStep > 1,
                ),
                const SizedBox(height: 14),
                _buildStepRow(
                  stepNum: 2,
                  title: 'Optical Character Recognition (OCR)',
                  subtitle: 'Extracted text blocks & 2D spatial coordinates',
                  isActive: currentStep == 2,
                  isDone: currentStep > 2,
                ),
                const SizedBox(height: 14),
                _buildStepRow(
                  stepNum: 3,
                  title: 'Evaluating 10 Statutory Declarations',
                  subtitle: 'Checking Rule 6(1)(a)-(i) & font size Rule 6(3)',
                  isActive: currentStep == 3,
                  isDone: currentStep > 3,
                ),
                const SizedBox(height: 14),
                _buildStepRow(
                  stepNum: 4,
                  title: 'Compiling Form 1 Inspection Notice',
                  subtitle: 'Geo-tagged evidence record generated',
                  isActive: currentStep == 4,
                  isDone: currentStep > 4,
                ),

                const Spacer(),
                Text(
                  '<30-SECOND COMPLIANCE SLA ACTIVE',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: AppColors.saffronLight.withOpacity(0.9),
                    letterSpacing: 1.0,
                  ),
                ),
                const SizedBox(height: 12),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStepRow({
    required int stepNum,
    required String title,
    required String subtitle,
    required bool isActive,
    required bool isDone,
  }) {
    Color iconBg;
    Widget iconChild;

    if (isDone) {
      iconBg = AppColors.compliantGreen;
      iconChild = const Icon(Icons.check, size: 14, color: Colors.white);
    } else if (isActive) {
      iconBg = AppColors.saffron;
      iconChild = const SizedBox(
        width: 12,
        height: 12,
        child: CircularProgressIndicator(
          strokeWidth: 2,
          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
        ),
      );
    } else {
      iconBg = Colors.white.withOpacity(0.1);
      iconChild = Text(
        '$stepNum',
        style: const TextStyle(fontSize: 11, color: Colors.white60, fontWeight: FontWeight.bold),
      );
    }

    return Row(
      children: [
        Container(
          width: 26,
          height: 26,
          decoration: BoxDecoration(
            color: iconBg,
            shape: BoxShape.circle,
          ),
          child: Center(child: iconChild),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: isActive ? Colors.white : (isDone ? Colors.white70 : Colors.white38),
                ),
              ),
              Text(
                subtitle,
                style: TextStyle(
                  fontSize: 10,
                  color: Colors.white.withOpacity(0.5),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
