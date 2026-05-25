<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function fg_antraege_count_by_status( $status ) {
	$query = new WP_Query(
		array(
			'post_type'              => 'fg_antrag',
			'post_status'            => 'publish',
			'posts_per_page'         => 1,
			'fields'                 => 'ids',
			'meta_key'               => '_fg_antrag_status',
			'meta_value'             => $status,
			'no_found_rows'          => false,
			'update_post_meta_cache' => false,
			'update_post_term_cache' => false,
		)
	);

	return (int) $query->found_posts;
}

function fg_antraege_shortcode_counter() {
	$total      = (int) wp_count_posts( 'fg_antrag' )->publish;
	$accepted   = fg_antraege_count_by_status( 'angenommen' );
	$rejected   = fg_antraege_count_by_status( 'abgelehnt' );
	$submitted  = fg_antraege_count_by_status( 'eingereicht' );
	$cards      = array(
		__( 'Gesamt', 'fg-antraege' )      => $total,
		__( 'Angenommen', 'fg-antraege' )  => $accepted,
		__( 'Abgelehnt', 'fg-antraege' )   => $rejected,
		__( 'Eingereicht', 'fg-antraege' ) => $submitted,
	);
	$output     = '<div class="fg-antraege-counter">';

	foreach ( $cards as $label => $value ) {
		$output .= '<div class="fg-antraege-counter__card">';
		$output .= '<span class="fg-antraege-counter__value">' . esc_html( (string) $value ) . '</span>';
		$output .= '<span class="fg-antraege-counter__label">' . esc_html( $label ) . '</span>';
		$output .= '</div>';
	}

	$output .= '</div>';
	return $output;
}

function fg_antraege_label_for_status( $status ) {
	$labels = array(
		'eingereicht' => __( 'Eingereicht', 'fg-antraege' ),
		'angenommen'  => __( 'Angenommen', 'fg-antraege' ),
		'abgelehnt'   => __( 'Abgelehnt', 'fg-antraege' ),
	);

	return isset( $labels[ $status ] ) ? $labels[ $status ] : $labels['eingereicht'];
}

function fg_antraege_shortcode_liste() {
	$query = new WP_Query(
		array(
			'post_type'      => 'fg_antrag',
			'post_status'    => 'publish',
			'posts_per_page' => -1,
			'orderby'        => 'date',
			'order'          => 'DESC',
		)
	);

	if ( ! $query->have_posts() ) {
		return '<p>' . esc_html__( 'Es sind noch keine Anträge vorhanden.', 'fg-antraege' ) . '</p>';
	}

	ob_start();
	?>
	<div class="fg-antraege-list">
		<div class="fg-antraege-list__filters">
			<button type="button" class="fg-antraege-filter is-active" data-filter="alle"><?php esc_html_e( 'Alle', 'fg-antraege' ); ?></button>
			<button type="button" class="fg-antraege-filter" data-filter="eingereicht"><?php esc_html_e( 'Eingereicht', 'fg-antraege' ); ?></button>
			<button type="button" class="fg-antraege-filter" data-filter="angenommen"><?php esc_html_e( 'Angenommen', 'fg-antraege' ); ?></button>
			<button type="button" class="fg-antraege-filter" data-filter="abgelehnt"><?php esc_html_e( 'Abgelehnt', 'fg-antraege' ); ?></button>
		</div>
		<div class="fg-antraege-list__items">
			<?php
			while ( $query->have_posts() ) :
				$query->the_post();
				$post_id     = get_the_ID();
				$status      = (string) get_post_meta( $post_id, '_fg_antrag_status', true );
				$request_day = (string) get_post_meta( $post_id, '_fg_antrag_datum', true );
				$pdf_url     = (string) get_post_meta( $post_id, '_fg_antrag_pdf_url', true );
				$summary     = (string) get_post_meta( $post_id, '_fg_antrag_summary', true );

				if ( '' === $status ) {
					$status = 'eingereicht';
				}
				?>
				<article class="fg-antrag-item" data-status="<?php echo esc_attr( $status ); ?>">
					<button type="button" class="fg-antrag-item__toggle" aria-expanded="false">
						<span class="fg-antrag-item__title"><?php the_title(); ?></span>
						<span class="fg-antrag-item__status status-<?php echo esc_attr( $status ); ?>"><?php echo esc_html( fg_antraege_label_for_status( $status ) ); ?></span>
						<?php if ( '' !== $request_day ) : ?>
							<span class="fg-antrag-item__date"><?php echo esc_html( $request_day ); ?></span>
						<?php endif; ?>
					</button>
					<div class="fg-antrag-item__content" hidden>
						<?php if ( '' !== $summary ) : ?>
							<p><?php echo esc_html( $summary ); ?></p>
						<?php else : ?>
							<?php the_content(); ?>
						<?php endif; ?>
						<?php if ( '' !== $pdf_url ) : ?>
							<p><a href="<?php echo esc_url( $pdf_url ); ?>" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'PDF öffnen', 'fg-antraege' ); ?></a></p>
						<?php endif; ?>
					</div>
				</article>
			<?php endwhile; ?>
		</div>
	</div>
	<?php
	wp_reset_postdata();

	return (string) ob_get_clean();
}

add_shortcode( 'fg_antraege_counter', 'fg_antraege_shortcode_counter' );
add_shortcode( 'fg_antraege_liste', 'fg_antraege_shortcode_liste' );
