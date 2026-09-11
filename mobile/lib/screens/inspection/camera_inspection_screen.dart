import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/scan_provider.dart';
import '../../widgets/capture_tray.dart';

class CameraInspectionScreen extends ConsumerStatefulWidget {
  const CameraInspectionScreen({super.key});

  @override
  ConsumerState<CameraInspectionScreen> createState() => _CameraInspectionScreenState();
}

class _CameraInspectionScreenState extends ConsumerState<CameraInspectionScreen> {
  final ImagePicker _picker = ImagePicker();
  final List<String?> _panelImages = List.filled(6, null);
  int _activeSlotIndex = 0;

  static const List<String> _panelKeys = [
    'front',
    'back',
    'mrp_panel',
    'side',
    'side',
    'other',
  ];

  static const List<String> _panelNames = [
    'Front Panel (PDP)',
    'Back / Info Panel',
    'MRP & Net Qty Panel',
    'Side Panel 1',
    'Side Panel 2',
    'Base / Reference Panel',
  ];

  static const List<String> _panelInstructions = [
    'Align Principal Display Panel with brand & commodity name',
    'Align Manufacturer / Packer name & complete address',
    'Align MRP, inclusive of taxes, Net Quantity & Dates',
    'Align Consumer care email, phone & ingredients',
    'Align Barcode, batch number & statutory marks',
    'Align Base, seal, or secondary statutory panel',
  ];

  Future<void> _captureFromCamera() async {
    if (!kIsWeb && Platform.isAndroid) {
      final status = await Permission.camera.request();
      if (!status.isGranted) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Camera permission required. You can also pick from Gallery.'),
              backgroundColor: AppColors.violationRed,
            ),
          );
        }
        return;
      }
    }

    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 88,
      );

      if (photo != null) {
        setState(() {
          _panelImages[_activeSlotIndex] = photo.path;
          // Auto-advance to next empty slot if any
          final nextEmpty = _panelImages.indexWhere((p) => p == null || p.isEmpty);
          if (nextEmpty != -1) {
            _activeSlotIndex = nextEmpty;
          }
        });
      }
    } catch (e) {
      debugPrint('[Camera] Camera capture error: $e');
    }
  }

  Future<void> _pickFromGallery() async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 88,
      );

      if (photo != null) {
        setState(() {
          _panelImages[_activeSlotIndex] = photo.path;
          // Auto-advance to next empty slot if any
          final nextEmpty = _panelImages.indexWhere((p) => p == null || p.isEmpty);
          if (nextEmpty != -1) {
            _activeSlotIndex = nextEmpty;
          }
        });
      }
    } catch (e) {
      debugPrint('[Gallery] Pick error: $e');
    }
  }

  Future<void> _loadDemoSample() async {
    try {
      final tempDir = await getTemporaryDirectory();
      // Valid JPEG header & minimal image stream so real backend OCR / PaddleOCR can read bytes cleanly
      const validPixelJpeg = <int>[
        0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48,
        0x00, 0x48, 0x00, 0x00, 0xff, 0xdb, 0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0a, 0x0c, 0x14, 0x0d, 0x0c, 0x0b, 0x0b, 0x0c, 0x19, 0x12,
        0x13, 0x0f, 0x14, 0x1d, 0x1a, 0x1f, 0x1e, 0x1d, 0x1a, 0x1c, 0x1c, 0x20, 0x24, 0x2e, 0x27, 0x20,
        0x22, 0x2c, 0x23, 0x1c, 0x1c, 0x28, 0x37, 0x29, 0x2c, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1f, 0x27,
        0x39, 0x3d, 0x38, 0x32, 0x3c, 0x2e, 0x33, 0x34, 0x32, 0xff, 0xc0, 0x00, 0x0b, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xff, 0xc4, 0x00, 0x1f, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
        0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
        0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0xff, 0xda, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3f,
        0x00, 0xbf, 0x80, 0xff, 0xd9,
      ];

      for (int i = 0; i < 6; i++) {
        final samplePath = '${tempDir.path}/metroscan_sample_panel_${i + 1}.jpg';
        final f = File(samplePath);
        if (!f.existsSync()) {
          await f.writeAsBytes(validPixelJpeg);
        }
        _panelImages[i] = samplePath;
      }
      setState(() {
        _activeSlotIndex = 0;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('6 Sample panels loaded for testing'),
            duration: Duration(seconds: 2),
            backgroundColor: AppColors.primaryBlue,
          ),
        );
      }
    } catch (e) {
      debugPrint('[Demo] Sample load error: $e');
    }
  }

  void _clearImage(int index) {
    setState(() {
      _panelImages[index] = null;
    });
  }

  void _clearAllImages() {
    setState(() {
      for (int i = 0; i < 6; i++) {
        _panelImages[i] = null;
      }
      _activeSlotIndex = 0;
    });
  }

  void _onFindDetailsPressed() {
    final images = <String>[];
    final panelTypes = <String>[];

    for (int i = 0; i < 6; i++) {
      final path = _panelImages[i];
      if (path != null && path.isNotEmpty) {
        images.add(path);
        panelTypes.add(_panelKeys[i]);
      }
    }

    if (images.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please capture at least one package panel photo'),
          backgroundColor: AppColors.violationRed,
        ),
      );
      return;
    }

    ref.read(capturedImagesProvider.notifier).state = images;
    ref.read(capturedPanelTypesProvider.notifier).state = panelTypes;
    context.push('/processing');
  }

  @override
  Widget build(BuildContext context) {
    final activeImagePath = _panelImages[_activeSlotIndex];
    final bool hasActiveImage = activeImagePath != null && activeImagePath.isNotEmpty;
    final int totalCaptured = _panelImages.where((p) => p != null && p.isNotEmpty).length;
    final activePanelName = _panelNames[_activeSlotIndex];
    final activeInstruction = _panelInstructions[_activeSlotIndex];

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: SafeArea(
        child: Column(
          children: [
            // 1. Top Header Bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: const Color(0xFF0B1120),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 20),
                    tooltip: 'Back',
                    onPressed: () {
                      if (context.canPop()) {
                        context.pop();
                      } else {
                        context.go('/dashboard');
                      }
                    },
                  ),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Package Inspection',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        Text(
                          'Legal Metrology Compliance Check',
                          style: TextStyle(
                            color: Colors.white70,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                  // Multi-Panel Status Badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: totalCaptured > 0 ? AppColors.compliantGreen : const Color(0xFF334155),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          totalCaptured > 0 ? Icons.check_circle_rounded : Icons.camera_alt_rounded,
                          color: Colors.white,
                          size: 13,
                        ),
                        const SizedBox(width: 5),
                        Text(
                          '$totalCaptured/6 Panels',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // 2. Central Viewfinder / Active Panel Photo Display
            Expanded(
              child: Container(
                margin: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(22),
                  border: Border.all(
                    color: hasActiveImage ? AppColors.compliantGreen : Colors.white24,
                    width: 2.2,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.4),
                      blurRadius: 16,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                clipBehavior: Clip.antiAlias,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    // A. Active panel photo preview
                    if (hasActiveImage)
                      Positioned.fill(
                        child: _buildCapturedImagePreview(activeImagePath),
                      )
                    // B. Framing viewfinder guide for active slot
                    else
                      Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(18),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.06),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.camera_alt_rounded,
                                color: AppColors.saffronLight,
                                size: 54,
                              ),
                            ),
                            const SizedBox(height: 14),
                            Text(
                              'Panel ${_activeSlotIndex + 1}: $activePanelName',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.w900,
                              ),
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 6),
                            Text(
                              activeInstruction,
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.65),
                                fontSize: 12,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),

                    // C. Framing Corner Reticles
                    if (!hasActiveImage) ...[
                      Positioned(top: 20, left: 20, child: _bracketCorner(0)),
                      Positioned(top: 20, right: 20, child: _bracketCorner(1)),
                      Positioned(bottom: 20, left: 20, child: _bracketCorner(2)),
                      Positioned(bottom: 20, right: 20, child: _bracketCorner(3)),
                    ],

                    // D. Top Overlay Badge when image is captured
                    if (hasActiveImage)
                      Positioned(
                        top: 12,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.85),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: AppColors.compliantGreen, width: 1.5),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.check_circle_rounded, color: AppColors.compliantGreen, size: 15),
                              const SizedBox(width: 6),
                              Text(
                                'Panel ${_activeSlotIndex + 1}: $activePanelName Ready',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),

            // 3. Evidence Tray (6 Canonical Slots)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: CaptureTray(
                panelImages: _panelImages,
                activeIndex: _activeSlotIndex,
                onSlotTapped: (idx) {
                  setState(() => _activeSlotIndex = idx);
                },
                onDeleteImage: (idx) {
                  _clearImage(idx);
                },
              ),
            ),

            // 4. Quick Controls Bar (Gallery / Shutter / Clear or Sample)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  // Pick from Gallery
                  InkWell(
                    onTap: _pickFromGallery,
                    borderRadius: BorderRadius.circular(16),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.white24),
                      ),
                      child: const Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.photo_library_rounded, color: Colors.white, size: 22),
                          SizedBox(height: 4),
                          Text(
                            'Gallery',
                            style: TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.w700),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Main Shutter Button
                  GestureDetector(
                    onTap: _captureFromCamera,
                    child: Container(
                      width: 72,
                      height: 72,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white,
                        border: Border.all(color: AppColors.saffron, width: 4),
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.saffron.withOpacity(0.4),
                            blurRadius: 18,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: const Center(
                        child: Icon(
                          Icons.camera_alt_rounded,
                          color: AppColors.sovereignDark,
                          size: 32,
                        ),
                      ),
                    ),
                  ),

                  // Quick Demo Sample or Clear
                  InkWell(
                    onTap: hasActiveImage
                        ? () => _clearImage(_activeSlotIndex)
                        : (totalCaptured > 0 ? _clearAllImages : _loadDemoSample),
                    borderRadius: BorderRadius.circular(16),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.white24),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            hasActiveImage ? Icons.delete_outline_rounded : Icons.auto_fix_high_rounded,
                            color: hasActiveImage ? AppColors.violationRed : AppColors.saffronLight,
                            size: 22,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            hasActiveImage ? 'Clear Slot' : (totalCaptured > 0 ? 'Clear All' : 'Sample'),
                            style: TextStyle(
                              color: hasActiveImage ? AppColors.violationRed : Colors.white70,
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // 5. Action Button: "Find Details" / "Analyze Panels"
            Container(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 14),
              child: SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: totalCaptured > 0 ? _onFindDetailsPressed : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.compliantGreen,
                    disabledBackgroundColor: const Color(0xFF334155),
                    elevation: totalCaptured > 0 ? 4 : 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.search_rounded,
                        color: totalCaptured > 0 ? Colors.white : Colors.white38,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        totalCaptured > 0
                            ? 'Find Details ($totalCaptured/6 Panels)'
                            : 'Find Details (Capture Photos)',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w900,
                          color: totalCaptured > 0 ? Colors.white : Colors.white38,
                          letterSpacing: 0.3,
                        ),
                      ),
                      if (totalCaptured > 0) ...[
                        const SizedBox(width: 8),
                        const Icon(Icons.arrow_forward_rounded, color: Colors.white, size: 18),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCapturedImagePreview(String path) {
    if (File(path).existsSync()) {
      return Image.file(
        File(path),
        fit: BoxFit.contain,
        errorBuilder: (_, __, ___) => _buildDemoPlaceholder(path),
      );
    }
    return _buildDemoPlaceholder(path);
  }

  Widget _buildDemoPlaceholder(String path) {
    return Container(
      color: const Color(0xFF1E293B),
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: const BoxDecoration(
              color: AppColors.compliantGreenLight,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.inventory_2_rounded,
              color: AppColors.compliantGreen,
              size: 48,
            ),
          ),
          const SizedBox(height: 14),
          const Text(
            'Panel Image Ready',
            style: TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            path,
            style: const TextStyle(
              color: Colors.white60,
              fontSize: 11,
              fontFamily: 'monospace',
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _bracketCorner(int corner) {
    // 0: top-left, 1: top-right, 2: bottom-left, 3: bottom-right
    return Container(
      width: 24,
      height: 24,
      decoration: BoxDecoration(
        border: Border(
          top: (corner == 0 || corner == 1)
              ? const BorderSide(color: AppColors.saffronLight, width: 3)
              : BorderSide.none,
          bottom: (corner == 2 || corner == 3)
              ? const BorderSide(color: AppColors.saffronLight, width: 3)
              : BorderSide.none,
          left: (corner == 0 || corner == 2)
              ? const BorderSide(color: AppColors.saffronLight, width: 3)
              : BorderSide.none,
          right: (corner == 1 || corner == 3)
              ? const BorderSide(color: AppColors.saffronLight, width: 3)
              : BorderSide.none,
        ),
      ),
    );
  }
}
