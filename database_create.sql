CREATE TABLE `currency_pairs` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`ticker` VARCHAR(25) NOT NULL,
	PRIMARY KEY (`id`)
);
CREATE TABLE `exchanges` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`name` VARCHAR(25) NOT NULL,
	PRIMARY KEY (`id`)
);
CREATE TABLE `candles` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`exchange` INT NOT NULL,
	`timestamp` TIMESTAMP NOT NULL,
	`currency_pair` INT NOT NULL,
	`candle_size` VARCHAR(5) NOT NULL,
	`open` DOUBLE NOT NULL,
	`high` DOUBLE NOT NULL,
	`low` DOUBLE NOT NULL,
	`close` DOUBLE NOT NULL,
	`volume` DOUBLE NOT NULL,
	KEY `pair_candle` (`exchange`, `currency_pair`, `candle_size`) USING HASH,
	PRIMARY KEY (`id`),
	FOREIGN KEY (currency_pair) REFERENCES currency_pairs(id),
	FOREIGN KEY (exchange) REFERENCES exchanges(id)
);
INSERT INTO exchanges (name)
VALUES ('binance');
ALTER TABLE candles
ADD CONSTRAINT candles UNIQUE(exchange, timestamp, currency_pair, candle_size);