import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

/// A tasteful, modern brand logo and identity widget for VisionX.
/// Displays an abstract optical aperture mark with a refined wordmark.
class BrandLogo extends StatelessWidget {
  final double size;
  final bool showWordmark;
  final bool showBadge;

  const BrandLogo({
    super.key,
    this.size = 64,
    this.showWordmark = true,
    this.showBadge = true,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final primaryTextColor = isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Emblem Container
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: isDark ? AppColors.darkSurfaceSecondary : AppColors.papayaWhip,
            borderRadius: BorderRadius.circular(size * 0.32),
            border: Border.all(
              color: isDark ? AppColors.darkInputBorder : AppColors.beige,
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: isDark
                    ? Colors.black.withValues(alpha: 0.25)
                    : AppColors.lightBronze.withValues(alpha: 0.12),
                blurRadius: 16,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Center(
            child: CustomPaint(
              size: Size(size * 0.58, size * 0.58),
              painter: _VisionXLogoPainter(isDark: isDark),
            ),
          ),
        ),

        if (showWordmark) ...[
          const SizedBox(height: 14),
          Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                'Vision',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -0.4,
                  color: primaryTextColor,
                ),
              ),
              const Text(
                'X',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.4,
                  color: AppColors.lightBronze,
                ),
              ),
            ],
          ),
        ],

        if (showBadge) ...[
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
            decoration: BoxDecoration(
              color: isDark
                  ? AppColors.drySage.withValues(alpha: 0.15)
                  : AppColors.beige.withValues(alpha: 0.7),
              borderRadius: BorderRadius.circular(100),
              border: Border.all(
                color: isDark
                    ? AppColors.drySage.withValues(alpha: 0.3)
                    : AppColors.drySage.withValues(alpha: 0.5),
                width: 0.8,
              ),
            ),
            child: Text(
              'INTELLIGENCE PLATFORM',
              style: TextStyle(
                fontSize: 9.5,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.2,
                color: isDark ? AppColors.drySage : AppColors.lightTextSecondary,
              ),
            ),
          ),
        ],
      ],
    );
  }
}

/// Custom painter for the VisionX geometric emblem.
/// Combines an abstract vision aperture/iris with an elegant 'X' dynamic.
class _VisionXLogoPainter extends CustomPainter {
  final bool isDark;

  _VisionXLogoPainter({required this.isDark});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    // Paint for outer aperture arcs (Dry Sage)
    final arcPaint = Paint()
      ..color = AppColors.drySage
      ..style = PaintingStyle.stroke
      ..strokeWidth = size.width * 0.11
      ..strokeCap = StrokeCap.round;

    // Top-left to bottom-right arc
    final rect = Rect.fromCircle(center: center, radius: radius * 0.82);
    canvas.drawArc(rect, 0.45 * 3.14159, 0.8 * 3.14159, false, arcPaint);
    canvas.drawArc(rect, 1.45 * 3.14159, 0.8 * 3.14159, false, arcPaint);

    // Accent diagonal beam (Light Bronze)
    final bronzePaint = Paint()
      ..color = AppColors.lightBronze
      ..style = PaintingStyle.stroke
      ..strokeWidth = size.width * 0.11
      ..strokeCap = StrokeCap.round;

    canvas.drawLine(
      Offset(center.dx - radius * 0.62, center.dy - radius * 0.62),
      Offset(center.dx + radius * 0.62, center.dy + radius * 0.62),
      bronzePaint,
    );

    // Center focal point / pupil
    final centerFill = Paint()
      ..color = isDark ? AppColors.beige : AppColors.cornsilk
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, radius * 0.28, centerFill);

    final centerDot = Paint()
      ..color = AppColors.lightBronze
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, radius * 0.14, centerDot);
  }

  @override
  bool shouldRepaint(covariant _VisionXLogoPainter oldDelegate) {
    return oldDelegate.isDark != isDark;
  }
}
