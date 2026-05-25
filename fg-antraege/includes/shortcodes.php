<?php

defined( 'ABSPATH' ) || exit;

/**
 * Assets laden.
 *
 * @return void
 */
function fg_antraege_enqueue_assets() {
	wp_enqueue_style( 'fg-antraege', FG_ANTRAEGE_URL . 'assets/fg-antraege.css', array(), FG_ANTRAEGE_VERSION );
	wp_enqueue_script( 'fg-antraege', FG_ANTRAEGE_URL . 'assets/fg-antraege.js', array(), FG_ANTRAEGE_VERSION, true );
}
add_action( 'wp_enqueue_scripts', 'fg_antraege_enqueue_assets' );

/**
 * Counter ausgeben.
 *
 * @return string
 */
function fg_antraege_counter_shortcode() {
	$all_ids = get_posts(
		array(
			'post_type'      => 'fg_antrag',
			'post_status'    => 'publish',
			'fields'         => 'ids',
			'posts_per_page' => -1,
		)
	);

	$total = count( $all_ids );

	$accepted = get_posts(
		array(
			'post_type'      => 'fg_antrag',
			'post_status'    => 'publish',
			'fields'         => 'ids',
			'posts_per_page' => -1,
			'meta_query'     => array(
				array(
					'key'   => '_fg_status',
					'value' => 'angenommen',
				),
			),
		)
	);

	$rejected = get_posts(
		array(
			'post_type'      => 'fg_antrag',
			'post_status'    => 'publish',
			'fields'         => 'ids',
			'posts_per_page' => -1,
			'meta_query'     => array(
				array(
					'key'   => '_fg_status',
					'value' => 'abgelehnt',
				),
			),
		)
	);

	$submitted = get_posts(
		array(
			'post_type'      => 'fg_antrag',
			'post_status'    => 'publish',
			'fields'         => 'ids',
			'posts_per_page' => -1,
			'meta_query'     => array(
				array(
					'key'   => '_fg_status',
					'value' => 'eingereicht',
				),
			),
		)
	);

	ob_start();
	?>
	<div class="fg-antraege-counter">
		<div class="fg-antraege-counter__item">
			<span class="fg-antraege-counter__number"><?php echo esc_html( (string) $total ); ?></span>
			<span class="fg-antraege-counter__label"><?php echo esc_html__( 'Gesamt', 'fg-antraege' ); ?></span>
		</div>
		<div class="fg-antraege-counter__item">
			<span class="fg-antraege-counter__number"><?php echo esc_html( (string) count( $accepted ) ); ?></span>
			<span class="fg-antraege-counter__label"><?php echo esc_html__( 'Angenommen', 'fg-antraege' ); ?></span>
		</div>
		<div class="fg-antraege-counter__item">
			<span class="fg-antraege-counter__number"><?php echo esc_html( (string) count( $rejected ) ); ?></span>
			<span class="fg-antraege-counter__label"><?php echo esc_html__( 'Abgelehnt', 'fg-antraege' ); ?></span>
		</div>
		<div class="fg-antraege-counter__item">
			<span class="fg-antraege-counter__number"><?php echo esc_html( (string) count( $submitted ) ); ?></span>
			<span class="fg-antraege-counter__label"><?php echo esc_html__( 'Eingereicht', 'fg-antraege' ); ?></span>
		</div>
	</div>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'fg_antraege_counter', 'fg_antraege_counter_shortcode' );

/**
 * Listenansicht ausgeben.
 *
 * @return string
 */
function fg_antraege_liste_shortcode() {
	$query = new WP_Query(
		array(
			'post_type'      => 'fg_antrag',
			'post_status'    => 'publish',
			'posts_per_page' => -1,
			'orderby'        => 'date',
			'order'          => 'DESC',
		)
	);

	ob_start();
	?>
	<div class="fg-antraege-list-wrapper">
		<div class="fg-antraege-filter">
			<button type="button" class="fg-antraege-filter__btn is-active" data-filter="alle"><?php echo esc_html__( 'Alle', 'fg-antraege' ); ?></button>
			<button type="button" class="fg-antraege-filter__btn" data-filter="eingereicht"><?php echo esc_html__( 'Eingereicht', 'fg-antraege' ); ?></button>
			<button type="button" class="fg-antraege-filter__btn" data-filter="angenommen"><?php echo esc_html__( 'Angenommen', 'fg-antraege' ); ?></button>
			<button type="button" class="fg-antraege-filter__btn" data-filter="abgelehnt"><?php echo esc_html__( 'Abgelehnt', 'fg-antraege' ); ?></button>
		</div>
		<div class="fg-antraege-list">
			<?php
			if ( $query->have_posts() ) :
				while ( $query->have_posts() ) :
					$query->the_post();
					$post_id = get_the_ID();
					$status  = get_post_meta( $post_id, '_fg_status', true );
					$pdf_url = get_post_meta( $post_id, '_fg_pdf_url', true );
					$status  = $status ? $status : 'eingereicht';
					?>
					<article class="fg-antrag-item" data-status="<?php echo esc_attr( $status ); ?>">
						<button type="button" class="fg-antrag-item__toggle">
							<span class="fg-antrag-item__title"><?php echo esc_html( get_the_title() ); ?></span>
							<span class="fg-antrag-item__status fg-antrag-item__status--<?php echo esc_attr( $status ); ?>"><?php echo esc_html( ucfirst( $status ) ); ?></span>
						</button>
						<div class="fg-antrag-item__body">
							<?php if ( has_excerpt() ) : ?>
								<p><?php echo esc_html( get_the_excerpt() ); ?></p>
							<?php endif; ?>
							<?php if ( ! empty( $pdf_url ) ) : ?>
								<p><a href="<?php echo esc_url( $pdf_url ); ?>" target="_blank" rel="noopener noreferrer"><?php echo esc_html__( 'PDF öffnen', 'fg-antraege' ); ?></a></p>
							<?php endif; ?>
							<?php echo wp_kses_post( apply_filters( 'the_content', get_the_content() ) ); ?>
						</div>
					</article>
					<?php
				endwhile;
				wp_reset_postdata();
			else :
				?>
				<p><?php echo esc_html__( 'Keine Anträge vorhanden.', 'fg-antraege' ); ?></p>
				<?php
			endif;
			?>
		</div>
	</div>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'fg_antraege_liste', 'fg_antraege_liste_shortcode' );
