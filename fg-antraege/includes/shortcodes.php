<?php
/**
 * Shortcodes for FG Anträge.
 *
 * [fg_antraege_counter] – shows counts per status.
 * [fg_antraege_liste]   – shows accordion list with filter buttons.
 *
 * @package FG_Antraege
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Helper: query all fg_antrag posts.
 *
 * @return WP_Post[] Array of post objects.
 */
function fg_antraege_get_all() {
	return get_posts(
		array(
			'post_type'      => 'fg_antrag',
			'post_status'    => 'publish',
			'posts_per_page' => -1,
			'orderby'        => 'meta_value',
			'meta_key'       => '_fg_antrag_datum',
			'meta_type'      => 'DATE',
			'order'          => 'DESC',
		)
	);
}

/* -----------------------------------------------------------------------
 * Shortcode: [fg_antraege_counter]
 * --------------------------------------------------------------------- */

/**
 * Render the counter boxes shortcode.
 *
 * @return string HTML output.
 */
function fg_antraege_counter_shortcode() {
	$posts = fg_antraege_get_all();

	$gesamt      = count( $posts );
	$angenommen  = 0;
	$abgelehnt   = 0;
	$eingereicht = 0;

	foreach ( $posts as $post ) {
		$status = get_post_meta( $post->ID, '_fg_antrag_status', true );
		switch ( $status ) {
			case 'angenommen':
				$angenommen++;
				break;
			case 'abgelehnt':
				$abgelehnt++;
				break;
			case 'eingereicht':
				$eingereicht++;
				break;
		}
	}

	ob_start();
	?>
	<div class="fg-antraege-counter">
		<div class="fg-antraege-counter-box">
			<span class="fg-antraege-counter-number"><?php echo esc_html( $gesamt ); ?></span>
			<span class="fg-antraege-counter-label"><?php esc_html_e( 'Gesamt', 'fg-antraege' ); ?></span>
		</div>
		<div class="fg-antraege-counter-box">
			<span class="fg-antraege-counter-number"><?php echo esc_html( $angenommen ); ?></span>
			<span class="fg-antraege-counter-label"><?php esc_html_e( 'Angenommen', 'fg-antraege' ); ?></span>
		</div>
		<div class="fg-antraege-counter-box">
			<span class="fg-antraege-counter-number"><?php echo esc_html( $abgelehnt ); ?></span>
			<span class="fg-antraege-counter-label"><?php esc_html_e( 'Abgelehnt', 'fg-antraege' ); ?></span>
		</div>
		<div class="fg-antraege-counter-box">
			<span class="fg-antraege-counter-number"><?php echo esc_html( $eingereicht ); ?></span>
			<span class="fg-antraege-counter-label"><?php esc_html_e( 'Eingereicht', 'fg-antraege' ); ?></span>
		</div>
	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'fg_antraege_counter', 'fg_antraege_counter_shortcode' );

/* -----------------------------------------------------------------------
 * Shortcode: [fg_antraege_liste]
 * --------------------------------------------------------------------- */

/**
 * Render the accordion list shortcode.
 *
 * @return string HTML output.
 */
function fg_antraege_liste_shortcode() {
	$posts = fg_antraege_get_all();

	$status_labels = array(
		'angenommen'  => __( 'Angenommen', 'fg-antraege' ),
		'abgelehnt'   => __( 'Abgelehnt', 'fg-antraege' ),
		'eingereicht' => __( 'Eingereicht', 'fg-antraege' ),
	);

	ob_start();
	?>
	<div class="fg-antraege-liste" id="fg-antraege-liste">
		<div class="fg-antraege-filter">
			<button class="fg-antraege-filter-btn active" data-filter="alle">
				<?php esc_html_e( 'Alle', 'fg-antraege' ); ?>
			</button>
			<button class="fg-antraege-filter-btn" data-filter="angenommen">
				<?php esc_html_e( 'Angenommen', 'fg-antraege' ); ?>
			</button>
			<button class="fg-antraege-filter-btn" data-filter="abgelehnt">
				<?php esc_html_e( 'Abgelehnt', 'fg-antraege' ); ?>
			</button>
			<button class="fg-antraege-filter-btn" data-filter="eingereicht">
				<?php esc_html_e( 'Eingereicht', 'fg-antraege' ); ?>
			</button>
		</div>

		<div class="fg-antraege-accordion">
			<?php if ( empty( $posts ) ) : ?>
				<p class="fg-antraege-empty">
					<?php esc_html_e( 'Keine Anträge vorhanden.', 'fg-antraege' ); ?>
				</p>
			<?php else : ?>
				<?php foreach ( $posts as $post ) : ?>
					<?php
					$status = get_post_meta( $post->ID, '_fg_antrag_status', true );
					if ( empty( $status ) ) {
						$status = 'eingereicht';
					}
					$datum  = get_post_meta( $post->ID, '_fg_antrag_datum', true );
					$pdf    = get_post_meta( $post->ID, '_fg_antrag_pdf', true );
					$label  = isset( $status_labels[ $status ] ) ? $status_labels[ $status ] : $status;
					?>
					<div class="fg-antraege-item" data-status="<?php echo esc_attr( $status ); ?>">
						<div class="fg-antraege-item-header">
							<span class="fg-antraege-item-title"><?php echo esc_html( $post->post_title ); ?></span>
							<span class="fg-antraege-status-badge fg-antraege-status-<?php echo esc_attr( $status ); ?>">
								<?php echo esc_html( $label ); ?>
							</span>
							<?php if ( ! empty( $datum ) ) : ?>
								<span class="fg-antraege-item-datum"><?php echo esc_html( $datum ); ?></span>
							<?php endif; ?>
							<span class="fg-antraege-toggle-icon">&#9660;</span>
						</div>
						<div class="fg-antraege-item-body">
							<?php if ( ! empty( $post->post_content ) ) : ?>
								<div class="fg-antraege-item-description">
									<?php echo wp_kses_post( wpautop( $post->post_content ) ); ?>
								</div>
							<?php endif; ?>
							<?php if ( ! empty( $pdf ) ) : ?>
								<a class="fg-antraege-pdf-link"
								   href="<?php echo esc_url( $pdf ); ?>"
								   target="_blank"
								   rel="noopener noreferrer">
									&#128196; <?php esc_html_e( 'PDF herunterladen', 'fg-antraege' ); ?>
								</a>
							<?php endif; ?>
						</div>
					</div>
				<?php endforeach; ?>
			<?php endif; ?>
		</div>
	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'fg_antraege_liste', 'fg_antraege_liste_shortcode' );
