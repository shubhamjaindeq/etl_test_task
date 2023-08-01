SELECT photographer_id, COUNT(*) AS num_photos
FROM photos
GROUP BY photographer_id
ORDER BY num_photos DESC
LIMIT 5;

select * from photos where avg_color like '#a%'

select avg(width), avg(height), photos.id from
photos inner join photo_sources
on photos.id = photo_sources.photo_id
group by photos.id