import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../core/constants/app_colors.dart';

class CaptureTray extends StatelessWidget {
  final List<String?> panelImages;
  final int activeIndex;
  final void Function(int index)? onSlotTapped;
  final void Function(int index)? onDeleteImage;
  final VoidCallback? onAddSlot;

  static const List<String> slotLabels = [
    'Front (PDP)',
    'Back / Info',
    'MRP & Dates',
    'Side 1',
    'Side 2',
    'Base / Other',
  ];

  static const List<IconData> slotIcons = [
    Icons.branding_watermark_rounded,
    Icons.receipt_long_rounded,
    Icons.sell_rounded,
    Icons.view_sidebar_rounded,
    Icons.view_sidebar_outlined,
    Icons.crop_free_rounded,
  ];

  const CaptureTray({
    super.key,
    required this.panelImages,
    this.activeIndex = 0,
    this.onSlotTapped,
    this.onDeleteImage,
    this.onAddSlot,
  });

  @override
  Widget build(BuildContext context) {
    final capturedCount = panelImages.where((p) => p != null && p.isNotEmpty).length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: capturedCount > 0 ? AppColors.compliantGreen : AppColors.textMuted,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '6-PANEL AUDIT TRAY ($capturedCount/6 CAPTURED)',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: Colors.white70,
                      letterSpacing: 0.5,
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 4),
              Flexible(
                child: Text(
                  'Panel ${activeIndex + 1}: ${slotLabels[activeIndex.clamp(0, 5)]}',
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: AppColors.saffronLight,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 94,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: 6,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (context, index) {
              final path = index < panelImages.length ? panelImages[index] : null;
              final hasImage = path != null && path.isNotEmpty;
              final isCurrent = index == activeIndex;
              final label = slotLabels[index];
              final icon = slotIcons[index];

              return GestureDetector(
                onTap: () => onSlotTapped?.call(index),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: 82,
                  decoration: BoxDecoration(
                    color: isCurrent
                        ? const Color(0xFF1E293B)
                        : (hasImage ? const Color(0xFF131D2E) : const Color(0xFF0F172A)),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isCurrent
                          ? AppColors.saffron
                          : (hasImage ? AppColors.compliantGreen.withOpacity(0.6) : Colors.white24),
                      width: isCurrent ? 2.2 : 1.2,
                    ),
                    boxShadow: isCurrent
                        ? [
                            BoxShadow(
                              color: AppColors.saffron.withOpacity(0.35),
                              blurRadius: 8,
                              offset: const Offset(0, 2),
                            )
                          ]
                        : null,
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(11),
                    child: Stack(
                      children: [
                        // Background Thumbnail if captured
                        if (hasImage && !kIsWeb && File(path).existsSync())
                          Positioned.fill(
                            child: Opacity(
                              opacity: 0.45,
                              child: Image.file(
                                File(path),
                                fit: BoxFit.cover,
                              ),
                            ),
                          ),

                        // Center Slot Content
                        Center(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                if (hasImage) ...[
                                  Container(
                                    padding: const EdgeInsets.all(3),
                                    decoration: const BoxDecoration(
                                      color: AppColors.compliantGreen,
                                      shape: BoxShape.circle,
                                    ),
                                    child: const Icon(
                                      Icons.check_rounded,
                                      color: Colors.white,
                                      size: 14,
                                    ),
                                  ),
                                  const SizedBox(height: 3),
                                  Text(
                                    'P${index + 1} Ready',
                                    style: const TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.w900,
                                      color: Colors.white,
                                    ),
                                  ),
                                ] else ...[
                                  Icon(
                                    icon,
                                    color: isCurrent ? AppColors.saffronLight : Colors.white38,
                                    size: 20,
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Slot ${index + 1}',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700,
                                      color: isCurrent ? AppColors.saffronLight : Colors.white54,
                                    ),
                                  ),
                                ],
                                const SizedBox(height: 2),
                                Text(
                                  label,
                                  style: TextStyle(
                                    fontSize: 9,
                                    fontWeight: isCurrent ? FontWeight.w800 : FontWeight.w500,
                                    color: isCurrent ? Colors.white : Colors.white60,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  textAlign: TextAlign.center,
                                ),
                              ],
                            ),
                          ),
                        ),

                        // Delete button when image is present
                        if (hasImage && onDeleteImage != null)
                          Positioned(
                            top: 3,
                            right: 3,
                            child: GestureDetector(
                              onTap: () => onDeleteImage?.call(index),
                              child: Container(
                                padding: const EdgeInsets.all(2),
                                decoration: const BoxDecoration(
                                  color: AppColors.violationRed,
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(Icons.close_rounded, size: 12, color: Colors.white),
                              ),
                            ),
                          ),

                        // Active slot indicator bar
                        if (isCurrent)
                          Positioned(
                            bottom: 0,
                            left: 0,
                            right: 0,
                            child: Container(
                              height: 3,
                              color: AppColors.saffron,
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
